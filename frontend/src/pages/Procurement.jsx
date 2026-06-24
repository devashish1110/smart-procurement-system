import { useState, useEffect } from 'react';
import { procurementAPI, vendorsAPI, medicinesAPI } from '../services/api';
import { useAuth } from '../contexts/AuthContext';
import { ShoppingCart, Plus, Check, X, Eye, Truck } from 'lucide-react';
import { formatCurrency, formatDate, getStatusColor } from '../utils/helpers';
import Loading from '../components/common/Loading';

const Procurement = () => {
  const { user } = useAuth();
  const [orders, setOrders] = useState([]);
  const [vendors, setVendors] = useState([]);
  const [medicines, setMedicines] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showCreateModal, setShowCreateModal] = useState(false);
  const [selectedOrder, setSelectedOrder] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [ordersRes, vendorsRes, medicinesRes, statsRes] = await Promise.all([
        procurementAPI.getAll(),
        vendorsAPI.getAll(),
        medicinesAPI.getAll(),
        procurementAPI.getStats()
      ]);

      setOrders(ordersRes.data);
      setVendors(vendorsRes.data);
      setMedicines(medicinesRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleApprove = async (poId) => {
    if (!window.confirm('Approve this purchase order?')) return;
    
    try {
      await procurementAPI.approve(poId);
      alert('Purchase order approved successfully!');
      loadData();
    } catch (error) {
      alert('Failed to approve order: ' + error.response?.data?.detail);
    }
  };

  const handleMarkOrdered = async (poId) => {
    if (!window.confirm('Mark this order as sent to vendor?')) return;
    
    try {
      await procurementAPI.markOrdered(poId);
      alert('Order marked as sent to vendor!');
      loadData();
    } catch (error) {
      alert('Failed to update order: ' + error.response?.data?.detail);
    }
  };

  if (loading) return <Loading />;

  const canCreatePO = ['admin', 'pharmacist'].includes(user?.role);
  const canApprovePO = ['admin', 'doctor'].includes(user?.role);

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
            Procurement Management
          </h1>
          <p style={{ color: '#6b7280' }}>
            Manage purchase orders and vendor relationships
          </p>
        </div>
        {canCreatePO && (
          <button
            onClick={() => setShowCreateModal(true)}
            className="btn btn-primary"
            style={{ gap: '8px' }}
          >
            <Plus size={20} />
            Create Purchase Order
          </button>
        )}
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(240px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Total Purchase Orders
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {stats?.total_purchase_orders || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Total Procurement Value
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {formatCurrency(stats?.total_procurement_value || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Pending Orders Value
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
            {formatCurrency(stats?.pending_orders_value || 0)}
          </h3>
        </div>
      </div>

      {/* Purchase Orders Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
          Purchase Orders
        </h3>
        <table className="table">
          <thead>
            <tr>
              <th>PO Number</th>
              <th>Vendor</th>
              <th>Order Date</th>
              <th>Delivery Date</th>
              <th>Total Amount</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {orders.length === 0 ? (
              <tr>
                <td colSpan="7" style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#6b7280' }}>No purchase orders found</p>
                </td>
              </tr>
            ) : (
              orders.map((order) => (
                <tr key={order.po_id}>
                  <td style={{ fontWeight: '600', fontFamily: 'monospace' }}>
                    {order.po_number}
                  </td>
                  <td>{vendors.find(v => v.vendor_id === order.vendor_id)?.vendor_name || '-'}</td>
                  <td>{formatDate(order.order_date)}</td>
                  <td>{formatDate(order.expected_delivery_date)}</td>
                  <td style={{ fontWeight: '600' }}>{formatCurrency(order.total_amount)}</td>
                  <td>
                    <span className={`badge ${getStatusColor(order.status)}`}>
                      {order.status}
                    </span>
                  </td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => setSelectedOrder(order)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '13px' }}
                      >
                        <Eye size={16} />
                      </button>
                      {canApprovePO && order.status === 'draft' && (
                        <button
                          onClick={() => handleApprove(order.po_id)}
                          className="btn btn-success"
                          style={{ padding: '6px 12px', fontSize: '13px' }}
                        >
                          <Check size={16} />
                        </button>
                      )}
                      {canCreatePO && order.status === 'approved' && (
                        <button
                          onClick={() => handleMarkOrdered(order.po_id)}
                          className="btn btn-primary"
                          style={{ padding: '6px 12px', fontSize: '13px' }}
                        >
                          <Truck size={16} />
                        </button>
                      )}
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Create PO Modal */}
      {showCreateModal && (
        <CreatePOModal
          vendors={vendors}
          medicines={medicines}
          onClose={() => setShowCreateModal(false)}
          onSuccess={() => {
            setShowCreateModal(false);
            loadData();
          }}
        />
      )}

      {/* View Order Modal */}
      {selectedOrder && (
        <ViewOrderModal
          order={selectedOrder}
          onClose={() => setSelectedOrder(null)}
        />
      )}
    </div>
  );
};

// Create PO Modal Component
const CreatePOModal = ({ vendors, medicines, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    vendor_id: '',
    expected_delivery_date: '',
    notes: '',
    items: [{ medicine_id: '', quantity_ordered: '', unit_price: '' }]
  });
  const [loading, setLoading] = useState(false);

  const addItem = () => {
    setFormData({
      ...formData,
      items: [...formData.items, { medicine_id: '', quantity_ordered: '', unit_price: '' }]
    });
  };

  const removeItem = (index) => {
    const newItems = formData.items.filter((_, i) => i !== index);
    setFormData({ ...formData, items: newItems });
  };

  const updateItem = (index, field, value) => {
    const newItems = [...formData.items];
    newItems[index][field] = value;
    setFormData({ ...formData, items: newItems });
  };

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await procurementAPI.create(formData);
      alert('Purchase order created successfully!');
      onSuccess();
    } catch (error) {
      alert('Failed to create order: ' + error.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const totalAmount = formData.items.reduce((sum, item) => {
    return sum + (parseFloat(item.quantity_ordered || 0) * parseFloat(item.unit_price || 0));
  }, 0);

  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '800px',
        width: '90%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Create Purchase Order</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Vendor */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Vendor *</label>
            <select
              className="input"
              value={formData.vendor_id}
              onChange={(e) => setFormData({ ...formData, vendor_id: e.target.value })}
              required
            >
              <option value="">Select Vendor</option>
              {vendors.map(v => (
                <option key={v.vendor_id} value={v.vendor_id}>
                  {v.vendor_name} (Rating: {v.rating}/5)
                </option>
              ))}
            </select>
          </div>

          {/* Expected Delivery Date */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Expected Delivery Date *</label>
            <input
              type="date"
              className="input"
              value={formData.expected_delivery_date}
              onChange={(e) => setFormData({ ...formData, expected_delivery_date: e.target.value })}
              required
            />
          </div>

          {/* Items */}
          <div style={{ marginBottom: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <label className="label">Order Items *</label>
              <button type="button" onClick={addItem} className="btn btn-secondary" style={{ padding: '6px 12px' }}>
                <Plus size={16} />
                Add Item
              </button>
            </div>

            {formData.items.map((item, index) => (
              <div key={index} style={{
                display: 'grid',
                gridTemplateColumns: '2fr 1fr 1fr auto',
                gap: '8px',
                marginBottom: '8px',
                padding: '12px',
                background: '#f9fafb',
                borderRadius: '6px'
              }}>
                <select
                  className="input"
                  value={item.medicine_id}
                  onChange={(e) => updateItem(index, 'medicine_id', e.target.value)}
                  required
                >
                  <option value="">Select Medicine</option>
                  {medicines.map(m => (
                    <option key={m.medicine_id} value={m.medicine_id}>
                      {m.medicine_name}
                    </option>
                  ))}
                </select>
                <input
                  type="number"
                  className="input"
                  placeholder="Quantity"
                  value={item.quantity_ordered}
                  onChange={(e) => updateItem(index, 'quantity_ordered', e.target.value)}
                  required
                  min="1"
                />
                <input
                  type="number"
                  className="input"
                  placeholder="Unit Price"
                  value={item.unit_price}
                  onChange={(e) => updateItem(index, 'unit_price', e.target.value)}
                  required
                  min="0"
                  step="0.01"
                />
                {formData.items.length > 1 && (
                  <button
                    type="button"
                    onClick={() => removeItem(index)}
                    style={{
                      background: '#fee2e2',
                      color: '#991b1b',
                      border: 'none',
                      borderRadius: '6px',
                      padding: '8px',
                      cursor: 'pointer'
                    }}
                  >
                    <X size={16} />
                  </button>
                )}
              </div>
            ))}
          </div>

          {/* Total */}
          <div style={{
            padding: '16px',
            background: '#eff6ff',
            borderRadius: '8px',
            marginBottom: '16px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: '600' }}>
              <span>Total Amount:</span>
              <span>{formatCurrency(totalAmount)}</span>
            </div>
          </div>

          {/* Notes */}
          <div style={{ marginBottom: '20px' }}>
            <label className="label">Notes</label>
            <textarea
              className="input"
              rows="3"
              value={formData.notes}
              onChange={(e) => setFormData({ ...formData, notes: e.target.value })}
              placeholder="Any additional notes..."
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Creating...' : 'Create Purchase Order'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// View Order Modal Component
const ViewOrderModal = ({ order, onClose }) => {
  return (
    <div style={{
      position: 'fixed',
      top: 0,
      left: 0,
      right: 0,
      bottom: 0,
      background: 'rgba(0,0,0,0.5)',
      display: 'flex',
      alignItems: 'center',
      justifyContent: 'center',
      zIndex: 1000
    }}>
      <div style={{
        background: 'white',
        borderRadius: '12px',
        padding: '24px',
        maxWidth: '600px',
        width: '90%'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Order Details</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ display: 'grid', gap: '12px' }}>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>PO Number:</span>
            <p style={{ fontWeight: '600', fontFamily: 'monospace' }}>{order.po_number}</p>
          </div>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Order Date:</span>
            <p style={{ fontWeight: '500' }}>{formatDate(order.order_date)}</p>
          </div>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Expected Delivery:</span>
            <p style={{ fontWeight: '500' }}>{formatDate(order.expected_delivery_date)}</p>
          </div>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Total Amount:</span>
            <p style={{ fontWeight: '600', fontSize: '18px' }}>{formatCurrency(order.total_amount)}</p>
          </div>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Status:</span>
            <p>
              <span className={`badge ${getStatusColor(order.status)}`}>
                {order.status}
              </span>
            </p>
          </div>
          {order.notes && (
            <div>
              <span style={{ color: '#6b7280', fontSize: '14px' }}>Notes:</span>
              <p style={{ whiteSpace: 'pre-wrap' }}>{order.notes}</p>
            </div>
          )}
        </div>

        <button onClick={onClose} className="btn btn-primary" style={{ width: '100%', marginTop: '20px' }}>
          Close
        </button>
      </div>
    </div>
  );
};

export default Procurement;