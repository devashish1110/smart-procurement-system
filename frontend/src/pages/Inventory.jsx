import { useState, useEffect } from 'react';
import { inventoryAPI } from '../services/api';
import { Package, AlertTriangle, Calendar, Search } from 'lucide-react';
import { formatDate, getStatusColor, getDaysUntilExpiry, formatCurrency } from '../utils/helpers';
import Loading from '../components/common/Loading';

const Inventory = () => {
  const [inventory, setInventory] = useState([]);
  const [stats, setStats] = useState(null);
  const [lowStock, setLowStock] = useState([]);
  const [expiring, setExpiring] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [activeTab, setActiveTab] = useState('all');

  useEffect(() => {
    loadInventoryData();
  }, []);

  const loadInventoryData = async () => {
    try {
      setLoading(true);
      const [inventoryRes, statsRes, lowStockRes, expiringRes] = await Promise.all([
        inventoryAPI.getWithDetails(),
        inventoryAPI.getStats(),
        inventoryAPI.getLowStock(),
        inventoryAPI.getExpiring(30)
      ]);

      setInventory(inventoryRes.data);
      setStats(statsRes.data);
      setLowStock(lowStockRes.data);
      setExpiring(expiringRes.data);
    } catch (error) {
      console.error('Failed to load inventory:', error);
    } finally {
      setLoading(false);
    }
  };

  const filteredInventory = inventory.filter(item => {
    const matchesSearch = item.medicine_name?.toLowerCase().includes(search.toLowerCase());
    
    if (activeTab === 'all') return matchesSearch;
    if (activeTab === 'low') return matchesSearch && item.status === 'low_stock';
    if (activeTab === 'expiring') {
      const days = getDaysUntilExpiry(item.expiry_date);
      return matchesSearch && days <= 30 && days >= 0;
    }
    return matchesSearch;
  });

  if (loading) return <Loading />;

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
          Inventory Management
        </h1>
        <p style={{ color: '#6b7280' }}>
          Monitor stock levels, expiry dates, and manage inventory
        </p>
      </div>

      {/* Stats Cards */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                Total Items
              </p>
              <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
                {stats?.total_stock_items || 0}
              </h3>
            </div>
            <Package size={24} color="#2563eb" />
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                Low Stock
              </p>
              <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
                {stats?.low_stock || 0}
              </h3>
            </div>
            <AlertTriangle size={24} color="#f59e0b" />
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                Expiring Soon
              </p>
              <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#ef4444' }}>
                {stats?.expiring_in_30_days || 0}
              </h3>
            </div>
            <Calendar size={24} color="#ef4444" />
          </div>
        </div>

        <div className="card">
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                Total Value
              </p>
              <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
                {formatCurrency(stats?.total_inventory_value || 0)}
              </h3>
            </div>
          </div>
        </div>
      </div>

      {/* Alerts */}
      {(lowStock.length > 0 || expiring.length > 0) && (
        <div style={{ display: 'grid', gap: '12px', marginBottom: '24px' }}>
          {lowStock.length > 0 && (
            <div className="alert alert-warning">
              <AlertTriangle size={18} />
              <span>
                <strong>{lowStock.length} medicines</strong> are below reorder level. 
                Consider creating purchase orders.
              </span>
            </div>
          )}
          {expiring.length > 0 && (
            <div className="alert alert-error">
              <Calendar size={18} />
              <span>
                <strong>{expiring.length} medicines</strong> are expiring within 30 days. 
                Prioritize dispensing these items.
              </span>
            </div>
          )}
        </div>
      )}

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{
          display: 'flex',
          gap: '16px',
          flexWrap: 'wrap',
          alignItems: 'center',
          justifyContent: 'space-between'
        }}>
          {/* Tabs */}
          <div style={{ display: 'flex', gap: '8px' }}>
            {[
              { key: 'all', label: 'All Items' },
              { key: 'low', label: 'Low Stock' },
              { key: 'expiring', label: 'Expiring Soon' }
            ].map(tab => (
              <button
                key={tab.key}
                onClick={() => setActiveTab(tab.key)}
                style={{
                  padding: '8px 16px',
                  background: activeTab === tab.key ? '#2563eb' : '#f3f4f6',
                  color: activeTab === tab.key ? 'white' : '#6b7280',
                  border: 'none',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontSize: '14px',
                  fontWeight: '500'
                }}
              >
                {tab.label}
              </button>
            ))}
          </div>

          {/* Search */}
          <div style={{ position: 'relative', flex: '1', minWidth: '300px' }}>
            <Search 
              size={18} 
              style={{
                position: 'absolute',
                left: '12px',
                top: '50%',
                transform: 'translateY(-50%)',
                color: '#9ca3af'
              }}
            />
            <input
              type="text"
              placeholder="Search medicines..."
              value={search}
              onChange={(e) => setSearch(e.target.value)}
              className="input"
              style={{ paddingLeft: '40px' }}
            />
          </div>
        </div>
      </div>

      {/* Inventory Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Medicine Name</th>
              <th>Category</th>
              <th>Batch Number</th>
              <th>Quantity</th>
              <th>Expiry Date</th>
              <th>Days to Expiry</th>
              <th>Status</th>
              <th>Vendor</th>
            </tr>
          </thead>
          <tbody>
            {filteredInventory.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#6b7280' }}>No inventory items found</p>
                </td>
              </tr>
            ) : (
              filteredInventory.map((item) => {
                const daysToExpiry = getDaysUntilExpiry(item.expiry_date);
                return (
                  <tr key={item.stock_id}>
                    <td style={{ fontWeight: '500' }}>{item.medicine_name}</td>
                    <td>{item.category || '-'}</td>
                    <td style={{ fontSize: '13px', fontFamily: 'monospace' }}>
                      {item.batch_number}
                    </td>
                    <td>
                      <span style={{
                        fontWeight: '600',
                        color: item.quantity_available <= 10 ? '#ef4444' : '#111827'
                      }}>
                        {item.quantity_available}
                      </span>
                    </td>
                    <td>{formatDate(item.expiry_date)}</td>
                    <td>
                      <span style={{
                        color: daysToExpiry < 30 ? '#ef4444' : 
                               daysToExpiry < 90 ? '#f59e0b' : '#10b981'
                      }}>
                        {daysToExpiry < 0 ? 'Expired' : `${daysToExpiry} days`}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${getStatusColor(item.status)}`}>
                        {item.status?.replace('_', ' ')}
                      </span>
                    </td>
                    <td style={{ fontSize: '13px' }}>{item.vendor_name || '-'}</td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Inventory;