import { Link } from 'react-router-dom';
import { Bot, Database, LineChart, Shield, Zap } from 'lucide-react';
import { useAuthStore } from '../store/authStore';

export const HomePage = () => {
  const isAuthenticated = useAuthStore((state) => state.isAuthenticated);

  const features = [
    {
      icon: Bot,
      title: 'NLU Training',
      description: 'Train powerful intent classification and entity recognition models',
    },
    {
      icon: Database,
      title: 'Dataset Management',
      description: 'Upload, manage, and analyze your training datasets efficiently',
    },
    {
      icon: LineChart,
      title: 'Model Evaluation',
      description: 'Evaluate and compare model performance with comprehensive metrics',
    },
    {
      icon: Zap,
      title: 'Active Learning',
      description: 'Continuously improve models with intelligent active learning',
    },
    {
      icon: Shield,
      title: 'Admin Controls',
      description: 'Manage users and workspaces with powerful admin tools',
    },
  ];

  return (
    <div className="min-h-screen">
      {/* Hero Section */}
      <div className="container mx-auto px-6 py-20">
        <div className="text-center max-w-4xl mx-auto">
          <h1 className="text-5xl md:text-6xl font-bold mb-6" style={{ color: '#f3f8ff' }}>
            Welcome to <span style={{ color: '#32f47a' }}>Bot Trainer</span> 🤖
          </h1>
          <p className="text-xl mb-8" style={{ color: 'rgba(228, 247, 238, 0.85)' }}>
            Design, launch, and manage conversational AI projects in a single secure workspace. 
            Train bots tailored to your team with powerful NLU capabilities.
          </p>

          <div className="flex gap-4 justify-center">
            {!isAuthenticated ? (
              <>
                <Link
                  to="/register"
                  className="btn-primary text-lg px-8 py-3"
                >
                  Create an Account
                </Link>
                <Link
                  to="/login"
                  className="btn-outline text-lg px-8 py-3"
                >
                  Access Your Workspace
                </Link>
              </>
            ) : (
              <Link
                to="/dashboard"
                className="btn-primary text-lg px-8 py-3"
              >
                Go to Dashboard
              </Link>
            )}
          </div>
        </div>

        {/* Features Grid */}
        <div className="mt-24 grid md:grid-cols-2 lg:grid-cols-3 gap-8">
          {features.map((feature, index) => (
            <div
              key={index}
              className="card-hover text-center"
            >
              <div className="inline-flex items-center justify-center w-16 h-16 rounded-full mb-4" style={{ background: 'rgba(50, 244, 122, 0.15)', color: 'var(--accent)' }}>
                <feature.icon size={32} />
              </div>
              <h3 className="text-xl font-bold mb-2" style={{ color: '#f3f8ff' }}>
                {feature.title}
              </h3>
              <p style={{ color: 'rgba(243, 248, 255, 0.75)' }}>{feature.description}</p>
            </div>
          ))}
        </div>

        {/* CTA Section */}
        <div className="mt-24 text-center rounded-2xl p-12 card">
          <h2 className="text-3xl font-bold mb-4" style={{ color: '#f3f8ff' }}>
            Ready to Build Your Bot?
          </h2>
          <p className="text-lg mb-6" style={{ color: 'rgba(50, 244, 122, 0.9)' }}>
            Join thousands of developers building intelligent conversational AI
          </p>
          {!isAuthenticated && (
            <Link
              to="/register"
              className="btn-primary inline-block px-8 py-3 rounded-lg font-semibold"
            >
              Get Started Free
            </Link>
          )}
        </div>
      </div>
    </div>
  );
};
