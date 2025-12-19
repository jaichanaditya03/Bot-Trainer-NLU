from fastapi import APIRouter, HTTPException, status, Header
from typing import Annotated, Optional, List, Dict, Any, Tuple
from pydantic import BaseModel
from auth import decode_token

# Lightweight runtime: spaCy for NER + rule-based intents (no transformers)
import os
from threading import Lock
import spacy
import json
from pathlib import Path

# Lazy spaCy model loader
_nlp = None
_nlp_lock = Lock()

# Optional lazy loaders for other engines
_rasa_loaded = False
_rasa_interpreter = None
_rasa_error: Optional[str] = None

_crf_loaded = False
_crf_model = None
_crf_error: Optional[str] = None

# Lightweight spaCy textcat trained per-session for evaluation
_spacy_textcat = None
_spacy_textcat_nlp = None

# Lightweight intent classifiers trained on-the-fly
_rasa_intent_model = None
_rasa_intent_labels: Optional[List[str]] = None

_nert_intent_model = None
_nert_intent_labels: Optional[List[str]] = None

def get_spacy_nlp():
    global _nlp
    if _nlp is None:
        with _nlp_lock:
            if _nlp is None:
                try:
                    # Prefer large model on Windows-friendly setup; allow override via SPACY_MODEL
                    preferred = os.environ.get("SPACY_MODEL")
                    candidates = [preferred] if preferred else [
                        "en_core_web_lg",
                        "en_core_web_md",
                        "en_core_web_sm",
                    ]
                    last_err = None
                    for name in candidates:
                        if not name:
                            continue
                        try:
                            _nlp = spacy.load(name)
                            break
                        except Exception as inner:
                            last_err = inner
                            _nlp = None
                    if _nlp is None:
                        raise RuntimeError(
                            f"No compatible spaCy model found. Tried: {candidates}. "
                            "Install models with: `python -m spacy download en_core_web_lg`, "
                            "`python -m spacy download en_core_web_md`, `python -m spacy download en_core_web_sm`. "
                            f"Last error: {last_err}"
                        )
                except Exception as e:
                    raise HTTPException(status_code=500, detail=f"Failed to load spaCy model: {e}")
    return _nlp


def _try_load_rasa():
    global _rasa_loaded, _rasa_interpreter, _rasa_error
    if _rasa_loaded:
        return _rasa_interpreter
    _rasa_loaded = True
    try:
        import importlib
        try:
            # Rasa 3.x
            from rasa.nlu.model import Interpreter  # type: ignore
            model_dir = Path("models") / "rasa"
            if not model_dir.exists():
                _rasa_error = "Rasa model directory models/rasa not found."
                return None
            # Try to load the directory directly; Rasa will resolve latest model inside
            _rasa_interpreter = Interpreter.load(str(model_dir))
            return _rasa_interpreter
        except Exception as e1:
            # Older API fallback (Rasa < 1.0)
            try:
                from rasa_nlu.model import Interpreter  # type: ignore
                model_dir = Path("models") / "rasa"
                _rasa_interpreter = Interpreter.load(str(model_dir))
                return _rasa_interpreter
            except Exception as e2:
                _rasa_error = (
                    "Rasa import failed in current environment. Either run a Rasa NLU server "
                    "and set RASA_SERVER_URL, or install Rasa in this runtime. "
                    f"Errors: rasa: {e1}; rasa_nlu: {e2}"
                )
                return None
    except Exception as e:
        _rasa_error = f"Rasa load failed: {e}"
        return None


def _rasa_parse_via_server(text: str) -> Optional[Dict[str, Any]]:
    """If RASA_SERVER_URL is set, call the server's /model/parse API.

    Returns the raw parse dict, or None if server URL not configured or request fails.
    """
    global _rasa_error
    server_url = os.environ.get("RASA_SERVER_URL", "").strip()
    if not server_url:
        return None
    # Normalize: allow base URL without path
    url = server_url
    if url.endswith("/"):
        url = url[:-1]
    if not url.endswith("/model/parse"):
        url = url + "/model/parse"
    try:
        import json as _json
        from urllib import request as _ureq
        data = _json.dumps({"text": text}).encode("utf-8")
        req = _ureq.Request(url, data=data, headers={"Content-Type": "application/json"}, method="POST")
        with _ureq.urlopen(req, timeout=10) as resp:
            if resp.status != 200:
                _rasa_error = f"Rasa server HTTP {resp.status}"
                return None
            body = resp.read().decode("utf-8")
            return json.loads(body)
    except Exception as e:
        _rasa_error = f"Rasa server request failed: {e}"
        return None


def _tokens_to_features(sent: str, tokens: List[str], i: int) -> Dict[str, Any]:
    w = tokens[i]
    prev = tokens[i - 1] if i > 0 else ""
    nxt = tokens[i + 1] if i < len(tokens) - 1 else ""
    return {
        "bias": 1.0,
        "word.lower()": w.lower(),
        "word.isupper()": w.isupper(),
        "word.istitle()": w.istitle(),
        "word.isdigit()": w.isdigit(),
        "prev.lower()": prev.lower(),
        "next.lower()": nxt.lower(),
        "BOS": i == 0,
        "EOS": i == len(tokens) - 1,
    }


def _try_load_crf():
    global _crf_loaded, _crf_model, _crf_error
    if _crf_loaded:
        return _crf_model
    _crf_loaded = True
    try:
        import joblib  # type: ignore
        model_path = Path("models") / "crf_ner" / "model.pkl"
        if not model_path.exists():
            _crf_error = "CRF model not found at models/crf_ner/model.pkl."
            return None
        _crf_model = joblib.load(model_path)
        return _crf_model
    except Exception as e:
        _crf_error = f"CRF load failed: {e}"
        return None

def _spacy_entities(text: str) -> List[Dict[str, Any]]:
    """Extract entities using spaCy English model (lg preferred, md/sm fallback).

    Returns list of dicts with keys: text,label,score,start,end
    """
    nlp = get_spacy_nlp()
    doc = nlp(text or "")
    ents: List[Dict[str, Any]] = []
    for ent in doc.ents:
        ents.append({
            "text": ent.text,
            "label": ent.label_,
            "score": 0.99,
            "start": int(ent.start_char),
            "end": int(ent.end_char),
        })
    return ents


router = APIRouter()

AuthorizationHeader = Annotated[Optional[str], Header(alias="Authorization")]


class PredictPayload(BaseModel):
    text: str
    model_id: Optional[str] = None  # engine: spacy|rasa|nert


class TrainSpacyIntentPayload(BaseModel):
    texts: List[str]
    labels: List[str]
    # epochs kept small for fast interactive training
    epochs: Optional[int] = 8


class TrainClassicIntentPayload(BaseModel):
    texts: List[str]
    labels: List[str]


class EntitySpanPayload(BaseModel):
    text: str
    label: str
    start: int
    end: int


class NertTrainingRecordPayload(BaseModel):
    text: str
    intent: str
    entities: List[EntitySpanPayload] = []


class TrainNertPayload(BaseModel):
    records: List[NertTrainingRecordPayload]


def _train_text_classifier(texts: List[str], labels: List[str]):
    if not texts or not labels or len(texts) != len(labels):
        raise ValueError("texts and labels must be non-empty and equal length")

    processed_texts = [str(t or "") for t in texts]
    processed_labels = [str(l or "").strip().lower() for l in labels]
    unique_labels = sorted(set(processed_labels))
    if not unique_labels:
        raise ValueError("No valid labels supplied")

    class _MajorityClassifier:
        def __init__(self, label: str):
            self.label = label
            self.classes_ = [label]

        def predict(self, items: List[str]):
            return [self.label for _ in items]

        def predict_proba(self, items: List[str]):
            return [[1.0] for _ in items]

    if len(unique_labels) == 1:
        return _MajorityClassifier(unique_labels[0]), unique_labels

    # Rasa-lite: use a different representation than NERT-lite so
    # its behavior is more distinct. Here we keep LogisticRegression
    # but switch from TF-IDF to simple binary bag-of-words with only
    # unigrams. This tends to emphasize presence/absence of words
    # rather than n-gram weights.
    from sklearn.pipeline import Pipeline  # type: ignore
    from sklearn.feature_extraction.text import CountVectorizer  # type: ignore
    from sklearn.linear_model import LogisticRegression  # type: ignore

    pipeline = Pipeline([
        ("bow", CountVectorizer(binary=True, ngram_range=(1, 1), min_df=1)),
        (
            "clf",
            LogisticRegression(
                max_iter=1000,
                class_weight="balanced",
                solver="lbfgs",
                multi_class="auto",
            ),
        ),
    ])

    pipeline.fit(processed_texts, processed_labels)

    classes = list(getattr(pipeline, "classes_", []))
    if not classes and hasattr(pipeline, "named_steps"):
        clf_step = pipeline.named_steps.get("clf")
        if clf_step is not None and hasattr(clf_step, "classes_"):
            classes = list(clf_step.classes_)

    if not classes:
        classes = unique_labels

    return pipeline, classes


def _extract_classes(model) -> List[str]:
    classes = list(getattr(model, "classes_", []))
    if classes:
        return [str(c) for c in classes]
    if hasattr(model, "named_steps"):
        clf_step = model.named_steps.get("clf")
        if clf_step is not None and hasattr(clf_step, "classes_"):
            return [str(c) for c in clf_step.classes_]
    return []


def _predict_with_confidence(model, text: str, default_confidence: float = 0.88) -> Tuple[str, float]:
    intent = model.predict([text])[0]
    intent_str = str(intent)
    confidence = default_confidence
    try:
        probabilities = model.predict_proba([text])[0]
        classes = _extract_classes(model)
        if classes and len(probabilities) == len(classes):
            try:
                idx = list(classes).index(intent_str)
                confidence = float(probabilities[idx])
            except ValueError:
                confidence = default_confidence
        elif len(probabilities) == 1:
            confidence = float(probabilities[0])
    except Exception:
        if _extract_classes(model) == [intent_str]:
            confidence = 1.0
    return intent_str, confidence


def _tokenize_for_crf(text: str) -> List[str]:
    try:
        import nltk  # type: ignore

        return nltk.word_tokenize(text)
    except Exception:
        return (text or "").split()


def _token_offsets(text: str, tokens: List[str]) -> List[Tuple[int, int]]:
    text_lower = (text or "").lower()
    offsets: List[Tuple[int, int]] = []
    cursor = 0
    for token in tokens:
        token_lower = token.lower()
        idx = text_lower.find(token_lower, cursor)
        if idx == -1:
            idx = text_lower.find(token_lower)
        if idx == -1:
            idx = cursor
        offsets.append((idx, idx + len(token)))
        cursor = max(idx + len(token), cursor + len(token))
    return offsets


def _spans_to_bio_tags(tokens: List[str], entities: List[Dict[str, Any]], text: str) -> List[str]:
    labels = ["O"] * len(tokens)
    if not tokens or not entities:
        return labels

    offsets = _token_offsets(text, tokens)
    for ent in entities:
        if ent is None:
            continue
        start = ent.get("start") if isinstance(ent, dict) else getattr(ent, "start", None)
        end = ent.get("end") if isinstance(ent, dict) else getattr(ent, "end", None)
        label = ent.get("label") if isinstance(ent, dict) else getattr(ent, "label", "")
        if start is None or end is None:
            continue
        start = int(start)
        end = int(end)
        if end <= start:
            continue
        label_str = str(label or "").strip().upper()
        if not label_str:
            continue
        token_indices = [i for i, (s, e) in enumerate(offsets) if e > start and s < end]
        if not token_indices:
            continue
        first = token_indices[0]
        labels[first] = f"B-{label_str}"
        for idx in token_indices[1:]:
            labels[idx] = f"I-{label_str}"
    return labels


def _bio_to_spans(tokens: List[str], labels: List[str], text: str) -> List[Dict[str, Any]]:
    if not tokens or not labels:
        return []

    offsets = _token_offsets(text, tokens)
    spans: List[Dict[str, Any]] = []
    i = 0
    while i < len(labels):
        tag = labels[i] or ""
        if not tag or tag == "O":
            i += 1
            continue
        if tag.startswith("B-"):
            label_core = tag[2:].lower()
            start = offsets[i][0]
            end = offsets[i][1]
            j = i + 1
            while j < len(labels) and labels[j] == f"I-{tag[2:]}":
                end = offsets[j][1]
                j += 1
            spans.append({
                "text": text[start:end],
                "label": label_core,
                "start": int(start),
                "end": int(end),
                "score": 0.9,
            })
            i = j
        else:
            i += 1
    return spans


@router.post("/train/intent/spacy", status_code=status.HTTP_200_OK)
def train_spacy_intent(payload: TrainSpacyIntentPayload, authorization: AuthorizationHeader = None):
    """Quickly train a spaCy textcat model in-memory for evaluation.

    This avoids heavyweight dependencies and matches the dataset the user loaded.
    """
    # Clear only spaCy model to allow retraining - preserve other models
    global _spacy_textcat, _spacy_textcat_nlp
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "")
    decode_token(token)

    # Only clear spaCy model, don't touch Rasa or NERT
    _spacy_textcat = None
    _spacy_textcat_nlp = None

    if not payload.texts or not payload.labels or len(payload.texts) != len(payload.labels):
        raise HTTPException(status_code=400, detail="texts and labels must be same length and non-empty")

    try:
        import spacy
        from spacy.util import minibatch
        nlp = spacy.blank("en")
        # Default config already fits single-label classification; keep it simple for compatibility
        textcat = nlp.add_pipe("textcat")

        labels = sorted({str(l).strip().lower() for l in payload.labels})
        for l in labels:
            textcat.add_label(l)

        # Prepare training examples
        examples = []
        for t, l in zip(payload.texts, payload.labels):
            cats = {lab: float(lab == str(l).strip().lower()) for lab in labels}
            examples.append((t or "", {"cats": cats}))

        optimizer = nlp.initialize(get_examples=lambda: (spacy.training.Example.from_dict(nlp.make_doc(t), ann) for t, ann in examples))
        epochs = int(payload.epochs or 8)
        for _ in range(max(1, epochs)):
            losses = {}
            import random
            random.shuffle(examples)
            batches = minibatch(examples, size=16)
            for batch in batches:
                exs = [spacy.training.Example.from_dict(nlp.make_doc(t), ann) for t, ann in batch]
                nlp.update(exs, sgd=optimizer, losses=losses)

        # Expose trained components globally for prediction
        _spacy_textcat = nlp.get_pipe("textcat")
        _spacy_textcat_nlp = nlp
        
        # Log training completion
        print(f"✅ spaCy model trained: {len(examples)} samples, {len(labels)} labels, {epochs} epochs")
        
        return {
            "labels": labels,
            "epochs": epochs,
            "training_samples": len(examples),
            "num_labels": len(labels)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"spaCy training failed: {e}")


@router.post("/train/intent/rasa-lite", status_code=status.HTTP_200_OK)
def train_rasa_intent(payload: TrainClassicIntentPayload, authorization: AuthorizationHeader = None):
    # Clear only Rasa model to allow retraining - preserve other models
    global _rasa_intent_model, _rasa_intent_labels
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "")
    decode_token(token)

    # Only clear Rasa model, don't touch spaCy or NERT
    _rasa_intent_model = None
    _rasa_intent_labels = None

    if not payload.texts or not payload.labels or len(payload.texts) != len(payload.labels):
        raise HTTPException(status_code=400, detail="texts and labels must be same length and non-empty")

    try:
        model, classes = _train_text_classifier(payload.texts, payload.labels)
        _rasa_intent_model = model
        _rasa_intent_labels = classes
        
        # Log training completion
        print(f"✅ Rasa model trained: {len(payload.texts)} samples, {len(classes)} labels")
        
        return {
            "labels": classes,
            "count": len(classes),
            "training_samples": len(payload.texts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rasa-lite training failed: {e}")


@router.post("/train/ner/nert-lite", status_code=status.HTTP_200_OK)
def train_nert(payload: TrainNertPayload, authorization: AuthorizationHeader = None):
    # Clear only NERT model and CRF to allow retraining - preserve other models
    global _nert_intent_model, _nert_intent_labels, _crf_model, _crf_loaded
    
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")
    token = authorization.replace("Bearer ", "")
    decode_token(token)

    # Only clear NERT and CRF models, don't touch spaCy or Rasa
    _nert_intent_model = None
    _nert_intent_labels = None
    _crf_model = None

    if not payload.records:
        raise HTTPException(status_code=400, detail="records must be non-empty")

    try:
        texts = [rec.text or "" for rec in payload.records]
        labels = [str(rec.intent or "").strip().lower() for rec in payload.records]

        # Use a different classifier for NERT-lite so it does not mirror
        # the Rasa-lite intent model. Here we keep the same TF-IDF features
        # but swap LogisticRegression for a linear SVM (LinearSVC).
        if not texts or not labels or len(texts) != len(labels):
            raise HTTPException(status_code=400, detail="texts and intents must be same length and non-empty")

        from sklearn.pipeline import Pipeline  # type: ignore
        from sklearn.feature_extraction.text import TfidfVectorizer  # type: ignore
        from sklearn.svm import LinearSVC  # type: ignore

        processed_texts = [str(t or "") for t in texts]
        processed_labels = [str(l or "").strip().lower() for l in labels]
        unique_labels = sorted(set(processed_labels))
        if not unique_labels:
            raise HTTPException(status_code=400, detail="No valid intent labels supplied")

        class _MajorityClassifier:
            def __init__(self, label: str):
                self.label = label
                self.classes_ = [label]

            def predict(self, items: List[str]):
                return [self.label for _ in items]

            def decision_function(self, items: List[str]):  # type: ignore[override]
                # Return a fixed positive margin for the single class
                import numpy as _np  # type: ignore
                return _np.ones((len(items), 1))

        if len(unique_labels) == 1:
            intent_model = _MajorityClassifier(unique_labels[0])
            classes = unique_labels
        else:
            intent_model = Pipeline([
                ("tfidf", TfidfVectorizer(ngram_range=(1, 2), min_df=1)),
                ("clf", LinearSVC()),
            ])
            intent_model.fit(processed_texts, processed_labels)
            classes = list(getattr(intent_model, "classes_", [])) or unique_labels

        _nert_intent_model = intent_model
        _nert_intent_labels = classes

        # Train CRF entities when annotations available
        crf_model = None
        any_entities = any(rec.entities for rec in payload.records)
        if any_entities:
            try:
                from sklearn_crfsuite import CRF  # type: ignore

                X_train: List[List[Dict[str, Any]]] = []
                y_train: List[List[str]] = []
                has_labeled_tokens = False
                for rec in payload.records:
                    tokens = _tokenize_for_crf(rec.text or "")
                    feats = [_tokens_to_features(rec.text or "", tokens, i) for i in range(len(tokens))]
                    spans = _spans_to_bio_tags(tokens, [ent.dict() for ent in rec.entities], rec.text or "")
                    if any(tag != "O" for tag in spans):
                        has_labeled_tokens = True
                    X_train.append(feats)
                    y_train.append(spans)
                if has_labeled_tokens and X_train:
                    crf_model = CRF(
                        algorithm="lbfgs",
                        c1=0.1,
                        c2=0.1,
                        max_iterations=100,
                        all_possible_transitions=True,
                    )
                    crf_model.fit(X_train, y_train)
            except Exception:
                crf_model = None

        if crf_model is not None:
            _crf_model = crf_model
            _crf_loaded = True

        # Log training completion
        print(f"✅ NERT model trained: {len(texts)} samples, {len(classes)} labels, CRF: {bool(crf_model)}")

        return {
            "labels": classes,
            "entity_model_trained": bool(crf_model),
            "label_count": len(classes),
            "training_samples": len(texts)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"NERT-lite training failed: {e}")


@router.post("/predict", status_code=status.HTTP_200_OK)
def predict(payload: PredictPayload, authorization: AuthorizationHeader = None):
    """
    Predict intent and entities using selected engine (spaCy/Rasa/NERT).

    Response format:
    {
      "intent": str,
      "entities": [
        {"entity": str, "word": str, "score": float}
      ]
    }
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Validate token (even if result is unused, it enforces auth)
    token = authorization.replace("Bearer ", "")
    decode_token(token)

    text = (payload.text or "").strip()
    if not text:
        raise HTTPException(status_code=400, detail="Text is required")

    engine = (payload.model_id or "spacy").lower()
    try:
        if engine == "rasa":
            if _rasa_intent_model is not None:
                # Use trained intent classifier
                classes = _extract_classes(_rasa_intent_model)
                default_conf = 0.95 if len(classes) > 1 else 1.0
                intent, confidence = _predict_with_confidence(_rasa_intent_model, text, default_conf)
                
                # Extract entities using CRF if available, otherwise use rules only
                entities: List[Dict[str, Any]] = []
                crf = _crf_model if _crf_model is not None else _try_load_crf()
                if crf:
                    try:
                        tokens = _tokenize_for_crf(text)
                        feats = [_tokens_to_features(text, tokens, i) for i in range(len(tokens))]
                        if hasattr(crf, "predict_marginals_single"):
                            marginals = crf.predict_marginals_single(feats)  # type: ignore
                            labels = []
                            for dist in marginals:
                                if isinstance(dist, dict) and dist:
                                    labels.append(max(dist.items(), key=lambda item: item[1])[0])
                                else:
                                    labels.append("O")
                        else:
                            labels = crf.predict([feats])[0]  # type: ignore
                        entities = _bio_to_spans(tokens, labels, text)
                    except Exception:
                        pass
                
                # Enrich with rule-based entities
                supplemental = _extract_travel_entities(text) + _extract_food_entities(text) + _extract_health_entities(text)
                entities = _deduplicate_entities(text, entities + supplemental)
                return {"intent": intent, "confidence": confidence, "entities": entities}

            # Prefer calling external Rasa server when configured
            res = _rasa_parse_via_server(text)
            if res is None:
                interp = _try_load_rasa()
                if not interp:
                    raise HTTPException(
                        status_code=503,
                        detail=(
                            "Rasa interpreter not available. Train via /train/intent/rasa-lite "
                            "or configure RASA_SERVER_URL to point to a running Rasa server."
                        ),
                    )
                res = interp.parse(text)  # type: ignore
            intent = (res.get("intent") or {}).get("name") or "unknown"
            confidence = float((res.get("intent") or {}).get("confidence") or 0.0)
            entities: List[Dict[str, Any]] = []
            for ent in res.get("entities", []):
                entities.append({
                    "text": ent.get("value") or ent.get("text") or "",
                    "label": ent.get("entity") or ent.get("type") or "other",
                    "start": int(ent.get("start") or 0),
                    "end": int(ent.get("end") or 0),
                    "score": float(ent.get("confidence_entity") or ent.get("confidence") or 0.0),
                })
            entities = _deduplicate_entities(text, entities)
            return {"intent": intent, "confidence": confidence, "entities": entities}

        if engine == "nert":
            if _nert_intent_model is None:
                raise HTTPException(
                    status_code=503,
                    detail="NERT intent model not trained. Call /train/ner/nert-lite before predicting.",
                )

            classes = _extract_classes(_nert_intent_model)
            default_conf = 0.9 if len(classes) > 1 else 1.0
            intent, confidence = _predict_with_confidence(_nert_intent_model, text, default_conf)

            # Extract entities using CRF if available
            entities: List[Dict[str, Any]] = []
            crf = _crf_model if _crf_model is not None else _try_load_crf()
            if crf:
                try:
                    tokens = _tokenize_for_crf(text)
                    feats = [_tokens_to_features(text, tokens, i) for i in range(len(tokens))]
                    if hasattr(crf, "predict_marginals_single"):
                        marginals = crf.predict_marginals_single(feats)  # type: ignore
                        labels = []
                        for dist in marginals:
                            if isinstance(dist, dict) and dist:
                                labels.append(max(dist.items(), key=lambda item: item[1])[0])
                            else:
                                labels.append("O")
                    else:
                        labels = crf.predict([feats])[0]  # type: ignore
                    # Convert BIO tags to entity spans
                    entities = _bio_to_spans(tokens, labels, text)
                except Exception as e:
                    # CRF prediction failed, entities will be rule-based only
                    pass

            # Always enrich with rule-based entities (even if CRF failed or not available)
            supplemental = _extract_travel_entities(text) + _extract_food_entities(text) + _extract_health_entities(text)
            entities = _deduplicate_entities(text, entities + supplemental)
            return {"intent": intent, "confidence": confidence, "entities": entities}

        if engine in {"intent", "hf", "transformer"}:
            # HF-based engines are no longer supported in this lightweight
            # runtime to avoid transformers/torch dependencies.
            raise HTTPException(
                status_code=503,
                detail="HF-based intent models are disabled in this deployment. Use 'spacy', 'rasa', or 'nert' engines instead.",
            )

        # Default: spaCy engine
        if _spacy_textcat is None or _spacy_textcat_nlp is None:
            raise HTTPException(
                status_code=503,
                detail="spaCy textcat model not trained. Call /train/intent/spacy before predicting.",
            )

        # If a trained textcat exists (from quick training), use it for intent
        spacy_ents = _spacy_entities(text)
        entities: List[Dict[str, Any]] = []
        min_entity_score = float(os.environ.get("MIN_ENTITY_SCORE", 0.0))
        for e in spacy_ents:
            if float(e.get("score", 0.0)) < min_entity_score:
                continue
            entities.append(e)
        # Enrich with rules
        entities = _deduplicate_entities(text, entities + _extract_travel_entities(text) + _extract_food_entities(text) + _extract_health_entities(text))
        doc = _spacy_textcat_nlp.make_doc(text)
        scores = _spacy_textcat.predict([doc])  # type: ignore
        if scores is None or len(scores) == 0:
            raise HTTPException(status_code=500, detail="spaCy intent model returned no scores")
        doc_scores = scores[0]
        label_data = _spacy_textcat.labels  # type: ignore[attr-defined]
        winner: Optional[Tuple[str, float]] = None
        if isinstance(doc_scores, dict):
            winner = max(doc_scores.items(), key=lambda kv: kv[1]) if doc_scores else None
        else:
            probs = list(doc_scores)
            if label_data and len(label_data) == len(probs):
                max_idx = int(probs.index(max(probs)))
                winner = (label_data[max_idx], float(probs[max_idx]))
        if winner is None:
            raise HTTPException(status_code=500, detail="Unable to determine intent from spaCy textcat scores")
        intent, confidence = winner[0], float(winner[1])
        return {"intent": intent, "confidence": confidence, "entities": entities}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Prediction failed: {e}")


class BatchPredictPayload(BaseModel):
    texts: List[str]
    model_id: Optional[str] = None  # Optional model ID to use for prediction
    allowed_intents: Optional[List[str]] = None  # Retained for backwards compatibility (no remapping)
    strict: Optional[bool] = False


@router.post("/predict/batch", status_code=status.HTTP_200_OK)
def predict_batch(payload: BatchPredictPayload, authorization: AuthorizationHeader = None):
    """
    Predict intents for multiple texts in batch (faster than individual calls).

    Response format:
    {
      "predictions": [
        {"text": str, "intent": str, "confidence": float},
        ...
      ]
    }
    """
    if not authorization:
        raise HTTPException(status_code=401, detail="Missing Authorization header")

    # Validate token
    token = authorization.replace("Bearer ", "")
    decode_token(token)

    if not payload.texts or len(payload.texts) == 0:
        raise HTTPException(status_code=400, detail="At least one text is required")

    try:
        engine = (payload.model_id or "spacy").lower()
        _ = bool(payload.strict)  # reserved for future use; predictions are always raw

        results = []
        for text in payload.texts:
            t = (text or "").strip()
            if not t:
                results.append({"text": t, "intent": "unknown", "confidence": 0.0})
                continue
            try:
                single = predict(PredictPayload(text=t, model_id=engine), authorization)
                raw_intent = str(single.get("intent", "unknown")).strip().lower()
                results.append({"text": t, "intent": raw_intent, "confidence": float(single.get("confidence", 0.0))})
            except Exception as e:
                results.append({"text": t, "intent": "error", "confidence": 0.0, "error": str(e)})

        return {"predictions": results}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Batch prediction failed: {e}")


def _extract_food_entities(text: str) -> List[Dict[str, Any]]:
    """Lightweight rule-based extraction for common food attributes.
    Produces entities with labels: food_item, quantity, size, beverage.
    """
    import re

    t = text or ""
    tl = t.lower()
    entities: List[Dict[str, Any]] = []

    # Food items and beverages vocabulary (extend as needed)
    vocab = {
        "food_item": [
            "pizza", "pepperoni pizza", "margherita", "burger", "veg burger", "chicken burger",
            "sandwich", "club sandwich", "fries", "biryani", "veg biryani", "chicken biryani",
            "noodles", "fried rice", "pasta", "taco", "wrap", "salad", "idli", "dosa", "paratha",
            "paneer", "butter chicken", "paneer tikka"
        ],
        "beverage": [
            "coffee", "tea", "coke", "pepsi", "sprite", "fanta", "juice", "lassi", "milkshake"
        ],
    }

    def add_span(text_sub: str, label: str, score: float = 0.99):
        start = tl.find(text_sub.lower())
        if start != -1:
            end = start + len(text_sub)
            entities.append({"text": t[start:end], "label": label, "score": score, "start": start, "end": end})

    # Items
    for label, words in vocab.items():
        for w in sorted(words, key=len, reverse=True):  # prefer longer phrases first
            add_span(w, label)

    # Quantity patterns: "2", "2x", "x2", "two", "double"
    qty_patterns = [
        r"(\d+)\s*(?:x|pcs|pieces|orders|plates)?",
        r"x\s*(\d+)",
    ]
    word_numbers = {
        "one": 1, "two": 2, "three": 3, "four": 4, "five": 5,
        "single": 1, "double": 2, "triple": 3
    }
    for pat in qty_patterns:
        for m in re.finditer(pat, tl):
            s, e = m.span()
            entities.append({"text": t[s:e], "label": "quantity", "score": 0.9, "start": s, "end": e})
    for w, n in word_numbers.items():
        if w in tl:
            add_span(w, "quantity", 0.9)

    # Size patterns
    for size in ["small", "medium", "large", "regular", "jumbo", "family"]:
        if size in tl:
            add_span(size, "size", 0.95)

    return entities


def _extract_health_entities(text: str) -> List[Dict[str, Any]]:
    """Rule-based extraction for common healthcare attributes.
    Labels: symptom, body_part, medication, dosage, frequency, duration, test_name, specialty, doctor_name.
    """
    import re

    t = text or ""
    tl = t.lower()
    entities: List[Dict[str, Any]] = []

    def add_span(sub: str, label: str, score: float = 0.98):
        i = tl.find(sub.lower())
        if i != -1:
            entities.append({"text": t[i:i+len(sub)], "label": label, "score": score, "start": i, "end": i+len(sub)})

    def add_span_word(word: str, label: str, score: float = 0.98):
        """Match a 'word' with strict alphabetic boundaries to avoid substring hits
        (e.g., 'ent' inside 'appointment').
        """
        pat = rf"(?<![A-Za-z]){re.escape(word)}(?![A-Za-z])"
        for m in re.finditer(pat, tl):
            s, e = m.span()
            entities.append({"text": t[s:e], "label": label, "score": score, "start": s, "end": e})

    # Vocab lists
    symptoms = [
        "fever", "cough", "cold", "flu", "headache", "migraine", "sore throat", "throat pain",
        "chest pain", "stomach ache", "abdominal pain", "back pain", "vomiting", "diarrhea", "dizziness",
        "fatigue", "rash"
    ]
    body_parts = ["head", "chest", "stomach", "abdomen", "back", "leg", "arm", "eye", "ear", "nose", "throat", "knee", "shoulder"]
    medications = [
        "paracetamol", "acetaminophen", "ibuprofen", "amoxicillin", "azithromycin", "metformin", "insulin",
        "aspirin", "omeprazole", "pantoprazole", "dolo 650", "crocin", "ciprofloxacin"
    ]
    tests = [
        "blood test", "cbc", "liver function test", "lft", "kidney function test", "kft", "x-ray", "ct scan", "mri",
        "ultrasound", "thyroid test", "tsh", "sugar test", "hba1c", "ecg"
    ]
    specialties = [
        "dermatology", "dermatologist", "cardiology", "cardiologist", "orthopedic", "orthopedics", "ent",
        "gynecology", "gynecologist", "pediatrics", "pediatrician", "neurologist", "neurology"
    ]

    for s in symptoms:
        add_span_word(s, "symptom")
    for bp in body_parts:
        add_span_word(bp, "body_part")
    # Longer medication names first; still enforce word boundaries
    for med in sorted(medications, key=len, reverse=True):
        add_span_word(med, "medication")
    for ts in sorted(tests, key=len, reverse=True):
        add_span_word(ts, "test_name")
    for sp in specialties:
        # 'ent' must be a standalone word to avoid matching 'appointment'
        if sp == "ent":
            add_span_word(sp, "specialty")
        else:
            add_span_word(sp, "specialty")

    # Dosage: 500 mg, 5mg, 1 tablet, 2 tablets
    for m in re.finditer(r"\b\d+\s*(?:mg|ml|mcg|g)\b", tl):
        s, e = m.span()
        entities.append({"text": t[s:e], "label": "dosage", "score": 0.95, "start": s, "end": e})
    for m in re.finditer(r"\b(\d+)\s*(?:tablet|tablets|capsule|capsules|puff|puffs|spoon|spoons)\b", tl):
        s, e = m.span()
        entities.append({"text": t[s:e], "label": "dosage", "score": 0.92, "start": s, "end": e})

    # Frequency: twice daily, every 8 hours, once a day
    freq_patterns = [
        r"\b(?:once|twice|thrice) (?:a |per )?(?:day|daily|week|month)\b",
        r"\bevery \d+ (?:hours|hour|days|day|weeks|week)\b",
    ]
    for pat in freq_patterns:
        for m in re.finditer(pat, tl):
            s, e = m.span()
            entities.append({"text": t[s:e], "label": "frequency", "score": 0.9, "start": s, "end": e})

    # Duration: for 5 days, 3 weeks
    for m in re.finditer(r"\bfor \d+ (?:days|day|weeks|week|months|month)\b", tl):
        s, e = m.span()
        entities.append({"text": t[s:e], "label": "duration", "score": 0.9, "start": s, "end": e})

    # Doctor Name: Dr. <Name>
    for m in re.finditer(r"\bdr\.?\s+[A-Z][a-z]+(?:\s+[A-Z][a-z]+)?\b", t):
        s, e = m.span()
        entities.append({"text": t[s:e], "label": "doctor_name", "score": 0.93, "start": s, "end": e})

    return entities


def _extract_travel_entities(text: str) -> List[Dict[str, Any]]:
    """Rule-based extraction for common travel attributes.
    Labels: source, destination, date, time, class, passenger_count, quota.
    """
    import re

    t = text or ""
    tl = t.lower()
    ents: List[Dict[str, Any]] = []

    def add_span(sub: str, label: str, score: float = 0.96):
        i = tl.find(sub.lower())
        if i != -1:
            ents.append({"text": t[i:i+len(sub)], "label": label, "score": score, "start": i, "end": i+len(sub)})

    def add_span_regex(pattern: str, label: str, score: float = 0.96):
        for m in re.finditer(pattern, tl):
            s, e = m.span()
            ents.append({"text": t[s:e], "label": label, "score": score, "start": s, "end": e})

    def _has_travel_context() -> bool:
        keywords = [
            "train", "railway", "bus", "coach", "flight", "plane", "airport", "station",
            "pnr", "ticket", "tickets", "booking", "reservation", "seat", "berth", "sleeper",
        ]
        return any(k in tl for k in keywords)

    # From/To pattern: from X to Y
    m = re.search(r"\bfrom\s+([a-zA-Z ]{2,40})\s+to\s+([a-zA-Z ]{2,40})\b", tl)
    if m:
        s1, s2 = m.span(1), m.span(2)
        ents.append({"text": t[s1[0]:s1[1]], "label": "source", "score": 0.97, "start": s1[0], "end": s1[1]})
        ents.append({"text": t[s2[0]:s2[1]], "label": "destination", "score": 0.97, "start": s2[0], "end": s2[1]})

    # To <city> (destination only)
    m = re.search(r"\bto\s+([a-zA-Z ]{2,40})\b", tl)
    if m:
        s = m.span(1)
        ents.append({"text": t[s[0]:s[1]], "label": "destination", "score": 0.95, "start": s[0], "end": s[1]})

    # On <date> (very loose)
    # Supports: 12/11/2025, 12-11-2025, 12 Nov, Nov 12, tomorrow, today, next monday
    date_patterns = [
        r"\b\d{1,2}[\/-]\d{1,2}(?:[\/-]\d{2,4})?\b",
        r"\b(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\s+\d{1,2}\b",
        r"\b\d{1,2}\s+(?:jan|feb|mar|apr|may|jun|jul|aug|sep|sept|oct|nov|dec)[a-z]*\b",
        r"\b(?:today|tomorrow|day after tomorrow|next\s+(?:mon|tue|wed|thu|thur|fri|sat|sun|monday|tuesday|wednesday|thursday|friday|saturday|sunday))\b",
    ]
    for pat in date_patterns:
        for m in re.finditer(pat, tl):
            s, e = m.span()
            ents.append({"text": t[s:e], "label": "date", "score": 0.9, "start": s, "end": e})

    # Time: 5 pm, 17:30
    time_patterns = [r"\b\d{1,2}:\d{2}\b", r"\b\d{1,2}\s*(?:am|pm)\b"]
    for pat in time_patterns:
        for m in re.finditer(pat, tl):
            s, e = m.span()
            ents.append({"text": t[s:e], "label": "time", "score": 0.9, "start": s, "end": e})

    # Class / quota (only when travel context is present)
    if _has_travel_context():
        for cls in ["economy", "business", "first class", "sleeper"]:
            if cls in tl:
                add_span(cls, "class", 0.92)
        # Strict patterns for AC classes to avoid matching inside words like "package"
        add_span_regex(r"\b3a\b", "class", 0.92)
        add_span_regex(r"\b2a\b", "class", 0.92)
        add_span_regex(r"\b1a\b", "class", 0.92)
        add_span_regex(r"\bac\b", "class", 0.92)
        add_span_regex(r"\bnon[ -]?ac\b", "class", 0.92)
        for q in ["tatkal", "premium tatkal", "ladies quota", "senior citizen", "general quota", "general"]:
            if q in tl:
                add_span(q, "quota", 0.9)

    # Passenger count
    for m in re.finditer(r"\b(\d+)\s*(?:passengers|passenger|people|persons|adults|kids|children)\b", tl):
        s, e = m.span()
        ents.append({"text": t[s:e], "label": "passenger_count", "score": 0.9, "start": s, "end": e})

    return ents


def _deduplicate_entities(source_text: str, entities: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Remove duplicate/overlapping entities keeping the highest-confidence, longest span.

    Dedup keys priority:
      1) (label, start, end) when offsets exist
      2) (label, normalized_text) as fallback
    If two spans with same label overlap heavily (IoU >= 0.8), keep the one with
    higher score, breaking ties by longer length.
    """
    if not entities:
        return []

    def norm_text(s: str) -> str:
        return (s or "").strip().strip("\"'.,;:!?)({}[]")

    # First pass: exact match by offsets
    by_key: Dict[Tuple, Dict[str, Any]] = {}
    for e in entities:
        lbl = str(e.get("label", "")).lower()
        start = e.get("start")
        end = e.get("end")
        if isinstance(start, int) and isinstance(end, int) and start >= 0 and end > start:
            key = (lbl, start, end)
        else:
            key = (lbl, norm_text(str(e.get("text", "")).lower()))
        prev = by_key.get(key)
        if not prev or float(e.get("score", 0.0)) > float(prev.get("score", 0.0)) or (
            float(e.get("score", 0.0)) == float(prev.get("score", 0.0)) and (e.get("end", 0) - e.get("start", 0)) > (prev.get("end", 0) - prev.get("start", 0))
        ):
            by_key[key] = e

    deduped = list(by_key.values())

    # Second pass: suppress heavy-overlap duplicates with same label
    def iou(a: Dict[str, Any], b: Dict[str, Any]) -> float:
        sa, ea = a.get("start"), a.get("end")
        sb, eb = b.get("start"), b.get("end")
        if None in (sa, ea, sb, eb):
            return 0.0
        inter = max(0, min(ea, eb) - max(sa, sb))
        if inter == 0:
            return 0.0
        union = (ea - sa) + (eb - sb) - inter
        return inter / union if union > 0 else 0.0

    deduped.sort(key=lambda x: float(x.get("score", 0.0)), reverse=True)
    final: List[Dict[str, Any]] = []
    for e in deduped:
        keep = True
        for f in final:
            if str(e.get("label")).lower() == str(f.get("label")).lower():
                if iou(e, f) >= 0.8:
                    keep = False
                    break
        if keep:
            # ensure start/end are ints when present
            if e.get("start") is not None:
                e["start"] = int(e["start"])
            if e.get("end") is not None:
                e["end"] = int(e["end"])
            final.append(e)

    return final
