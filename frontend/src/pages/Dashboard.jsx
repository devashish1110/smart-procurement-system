import { useState, useEffect } from 'react';
import { reportsAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { formatCurrency, getGreeting } from '../utils/helpers';
import { 
  Users, Package, ShoppingCart, DollarSign, 
  TrendingUp, AlertCircle, Calendar, FileText 
} from 'lucide-react';
import Loading from '../components/common/Loading';

const Dashboard = () => {
  const { user } = useAuth();
  const [data, setData] = useState(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState('');

  useEffect(() => {
    loadDashboardData();
  }, []);

  const loadDashboardData = async () => {
    try {
      setLoading(true);
      const response = await reportsAPI.getDashboard();
      setData(response.data);
    } catch (err) {
      setError('Failed to load dashboard data');
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading />;

  if (error) {
    return (
      <div className="alert alert-error">
        <AlertCircle size={18} />
        {error}
      </div>
    );
  }

  const stats = [
    {
      title: 'Total Patients',
      value: data?.patients?.total || 0,
      change: `+${data?.patients?.new_this_month || 0} this month`,
      icon: Users,
      color: '#2563eb',
      bgColor: '#eff6ff'
    },
    {
      title: 'Monthly Revenue',
      value: formatCurrency(data?.financial?.monthly_revenue || 0),
      change: formatCurrency(data?.financial?.todays_revenue || 0) + ' today',
      icon: DollarSign,
      color: '#10b981',
      bgColor: '#d1fae5'
    },
    {
      title: 'Low Stock Items',
      value: data?.inventory?.low_stock_items || 0,
      change: `${data?.inventory?.expiring_in_30_days || 0} expiring soon`,
      icon: Package,
      color: '#f59e0b',
      bgColor: '#fef3c7'
    },
    {
      title: 'Today\'s Appointments',
      value: data?.appointments?.today || 0,
      change: 'Scheduled visits',
      icon: Calendar,
      color: '#8b5cf6',
      bgColor: '#ede9fe'
    }
  ];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '32px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
          {getGreeting()}, {user?.full_name}!
        </h1>
        <p style={{ color: '#6b7280' }}>
          Here's what's happening with your clinic today
        </p>
      </div>

      {/* Stats Grid */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(280px, 1fr))',
        gap: '20px',
        marginBottom: '32px'
      }}>
        {stats.map((stat, index) => {
          const Icon = stat.icon;
          return (
            <div key={index} className="card" style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'flex-start'
            }}>
              <div style={{ flex: 1 }}>
                <p style={{
                  fontSize: '14px',
                  color: '#6b7280',
                  marginBottom: '8px'
                }}>
                  {stat.title}
                </p>
                <h3 style={{
                  fontSize: '32px',
                  fontWeight: '700',
                  marginBottom: '4px'
                }}>
                  {stat.value}
                </h3>
                <p style={{
                  fontSize: '13px',
                  color: '#10b981',
                  fontWeight: '500'
                }}>
                  {stat.change}
                </p>
              </div>
              <div style={{
                width: '60px',
                height: '60px',
                borderRadius: '12px',
                background: stat.bgColor,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center'
              }}>
                <Icon size={28} color={stat.color} />
              </div>
            </div>
          );
        })}
      </div>

      {/* Charts Row */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
        gap: '20px',
        marginBottom: '32px'
      }}>
        {/* Revenue Breakdown */}
        <div className="card">
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '20px'
          }}>
            Revenue Breakdown
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '12px' }}>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px',
              background: '#f9fafb',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '14px' }}>Consultation</span>
              <span style={{ fontWeight: '600' }}>
                {formatCurrency(data?.financial?.consultation_revenue || 0)}
              </span>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px',
              background: '#f9fafb',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '14px' }}>Medicine Sales</span>
              <span style={{ fontWeight: '600' }}>
                {formatCurrency(data?.financial?.medicine_revenue || 0)}
              </span>
            </div>
            <div style={{
              display: 'flex',
              justifyContent: 'space-between',
              alignItems: 'center',
              padding: '12px',
              background: '#f9fafb',
              borderRadius: '6px'
            }}>
              <span style={{ fontSize: '14px' }}>Treatments</span>
              <span style={{ fontWeight: '600' }}>
                {formatCurrency(data?.financial?.treatment_revenue || 0)}
              </span>
            </div>
          </div>
        </div>

        {/* Quick Actions */}
        <div className="card">
          <h3 style={{
            fontSize: '18px',
            fontWeight: '600',
            marginBottom: '20px'
          }}>
            Quick Actions
          </h3>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '10px' }}>
            <button className="btn btn-primary" style={{ width: '100%', justifyContent: 'flex-start' }}>
              <Calendar size={18} />
              Schedule Appointment
            </button>
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
              <FileText size={18} />
              Generate Bill
            </button>
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
              <ShoppingCart size={18} />
              Create Purchase Order
            </button>
            <button className="btn btn-secondary" style={{ width: '100%', justifyContent: 'flex-start' }}>
              <Package size={18} />
              Check Inventory
            </button>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {(data?.inventory?.low_stock_items > 0 || data?.inventory?.expiring_in_30_days > 0) && (
        <div className="card" style={{ background: '#fef3c7', borderColor: '#fcd34d' }}>
          <div style={{ display: 'flex', gap: '12px' }}>
            <AlertCircle size={24} color="#f59e0b" />
            <div>
              <h4 style={{ fontWeight: '600', marginBottom: '4px', color: '#92400e' }}>
                Inventory Alerts
              </h4>
              <p style={{ fontSize: '14px', color: '#92400e' }}>
                {data.inventory.low_stock_items} items are low in stock and {data.inventory.expiring_in_30_days} items are expiring within 30 days.
                Please review and take action.
              </p>
            </div>
          </div>
        </div>
      )}
    </div>
  );
};

export default Dashboard;