export const Card = ({ children, className = '', hover = false }) => {
  return (
    <div className={`${hover ? 'card-hover' : 'card'} ${className}`}>
      {children}
    </div>
  );
};

export const CardHeader = ({ title, subtitle, action }) => {
  return (
    <div className="flex justify-between items-start mb-4">
      <div>
        <h3 className="text-xl font-bold" style={{ color: '#f3f8ff' }}>{title}</h3>
        {subtitle && <p className="text-sm mt-1" style={{ color: 'rgba(228, 247, 238, 0.65)' }}>{subtitle}</p>}
      </div>
      {action && <div>{action}</div>}
    </div>
  );
};
