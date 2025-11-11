import { Link, useLocation } from 'react-router-dom';
import { 
  LayoutDashboard, Package, ShoppingCart, Users, 
  FileText, TrendingUp, MessageSquare, Settings,
  Calendar, DollarSign, AlertCircle
} from 'lucide-react';

const Sidebar = () => {
  const location = useLocation();

  const menuItems = [
    { path: '/dashboard', icon: LayoutDashboard, label: 'Dashboard' },
    { path: '/inventory', icon: Package, label: 'Inventory' },
    { path: '/procurement', icon: ShoppingCart, label: 'Procurement' },
    { path: '/patients', icon: Users, label: 'Patients' },
    { path: '/appointments', icon: Calendar, label: 'Appointments' },
    { path: '/billing', icon: DollarSign, label: 'Billing' },
    { path: '/reports', icon: TrendingUp, label: 'Reports' },
    { path: '/chatbot', icon: MessageSquare, label: 'AI Assistant' },
  ];

  const isActive = (path) => {
    return location.pathname === path || location.pathname.startsWith(path + '/');
  };

  return (
    <aside style={{
      width: '260px',
      background: 'white',
      borderRight: '1px solid #e5e7eb',
      height: 'calc(100vh - 65px)',
      position: 'sticky',
      top: '65px',
      overflowY: 'auto'
    }}>
      <nav style={{ padding: '16px 0' }}>
        {menuItems.map((item) => {
          const Icon = item.icon;
          const active = isActive(item.path);
          
          return (
            <Link
              key={item.path}
              to={item.path}
              style={{
                display: 'flex',
                alignItems: 'center',
                gap: '12px',
                padding: '12px 20px',
                color: active ? '#2563eb' : '#6b7280',
                background: active ? '#eff6ff' : 'transparent',
                borderLeft: active ? '3px solid #2563eb' : '3px solid transparent',
                textDecoration: 'none',
                fontSize: '14px',
                fontWeight: active ? '600' : '500',
                transition: 'all 0.2s',
                marginBottom: '2px'
              }}
              onMouseEnter={(e) => {
                if (!active) {
                  e.currentTarget.style.background = '#f9fafb';
                }
              }}
              onMouseLeave={(e) => {
                if (!active) {
                  e.currentTarget.style.background = 'transparent';
                }
              }}
            >
              <Icon size={20} />
              {item.label}
            </Link>
          );
        })}
      </nav>

      {/* Footer */}
      <div style={{
        position: 'absolute',
        bottom: 0,
        left: 0,
        right: 0,
        padding: '16px 20px',
        borderTop: '1px solid #e5e7eb',
        background: 'white'
      }}>
        <div style={{ fontSize: '12px', color: '#9ca3af', textAlign: 'center' }}>
          Version 1.0.0
        </div>
      </div>
    </aside>
  );
};

export default Sidebar;