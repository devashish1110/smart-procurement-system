import { useState, useEffect } from 'react';
import { billingAPI, patientsAPI } from '../services/api';
import { DollarSign, Plus, Eye, X } from 'lucide-react';
import { formatCurrency, formatDate } from '../utils/helpers';
import Loading from '../components/common/Loading';

const Billing = () => {
  const [bills, setBills] = useState([]);
  const [patients, setPatients] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [showModal, setShowModal] = useState(false);
  const [selectedBill, setSelectedBill] = useState(null);

  useEffect(() => {
    loadData();
  }, []);

  const loadData = async () => {
    try {
      setLoading(true);
      const [billsRes, patientsRes, statsRes] = await Promise.all([
        billingAPI.getAll({ limit: 100 }),
        patientsAPI.getAll({ limit: 1000 }),
        billingAPI.getStats()
      ]);

      setBills(billsRes.data);
      setPatients(patientsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  if (loading) return <Loading />;

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
            Billing & Payments
          </h1>
          <p style={{ color: '#6b7280' }}>
            Generate bills and track payments
          </p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn btn-primary" style={{ gap: '8px' }}>
          <Plus size={20} />
          Generate Bill
        </button>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(220px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Total Bills
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {stats?.total_bills || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Total Revenue
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#10b981' }}>
            {formatCurrency(stats?.total_revenue || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Total Collected
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#2563eb' }}>
            {formatCurrency(stats?.total_collected || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Outstanding
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
            {formatCurrency(stats?.total_outstanding || 0)}
          </h3>
        </div>
      </div>

      {/* Revenue Breakdown */}
      {stats?.revenue_breakdown && (
        <div className="card" style={{ marginBottom: '24px' }}>
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>
            Revenue Breakdown
          </h3>
          <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px' }}>
            <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '6px' }}>
              <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Consultation</p>
              <p style={{ fontSize: '20px', fontWeight: '600' }}>
                {formatCurrency(stats.revenue_breakdown.consultation)}
              </p>
            </div>
            <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '6px' }}>
              <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Medicine</p>
              <p style={{ fontSize: '20px', fontWeight: '600' }}>
                {formatCurrency(stats.revenue_breakdown.medicine)}
              </p>
            </div>
            <div style={{ padding: '12px', background: '#f9fafb', borderRadius: '6px' }}>
              <p style={{ fontSize: '13px', color: '#6b7280', marginBottom: '4px' }}>Treatment</p>
              <p style={{ fontSize: '20px', fontWeight: '600' }}>
                {formatCurrency(stats.revenue_breakdown.treatment)}
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Bills Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Bill Number</th>
              <th>Patient</th>
              <th>Date</th>
              <th>Total Amount</th>
              <th>Paid</th>
              <th>Balance</th>
              <th>Payment Mode</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {bills.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#6b7280' }}>No bills found</p>
                </td>
              </tr>
            ) : (
              bills.map((bill) => {
                const patient = patients.find(p => p.patient_id === bill.patient_id);
                return (
                  <tr key={bill.bill_id}>
                    <td style={{ fontWeight: '600', fontFamily: 'monospace' }}>
                      {bill.bill_number}
                    </td>
                    <td>{patient?.name || 'Unknown'}</td>
                    <td>{formatDate(bill.bill_date)}</td>
                    <td style={{ fontWeight: '600' }}>{formatCurrency(bill.total_amount)}</td>
                    <td style={{ color: '#10b981' }}>{formatCurrency(bill.amount_paid)}</td>
                    <td style={{ color: bill.balance > 0 ? '#f59e0b' : '#6b7280' }}>
                      {formatCurrency(bill.balance)}
                    </td>
                    <td>
                      <span className="badge badge-info" style={{ textTransform: 'uppercase' }}>
                        {bill.payment_mode}
                      </span>
                    </td>
                    <td>
                      <button
                        onClick={() => setSelectedBill(bill)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '13px' }}
                      >
                        <Eye size={16} />
                      </button>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Create Bill Modal */}
      {showModal && (
        <CreateBillModal
          patients={patients}
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            loadData();
          }}
        />
      )}

      {/* View Bill Modal */}
      {selectedBill && (
        <ViewBillModal
          bill={selectedBill}
          patient={patients.find(p => p.patient_id === selectedBill.patient_id)}
          onClose={() => setSelectedBill(null)}
        />
      )}
    </div>
  );
};

// Create Bill Modal
const CreateBillModal = ({ patients, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    patient_id: '',
    bill_date: new Date().toISOString().split('T')[0],
    consultation_charge: 0,
    medicine_charge: 0,
    treatment_charge: 0,
    payment_mode: 'cash'
  });
  const [loading, setLoading] = useState(false);

  const totalAmount = 
    parseFloat(formData.consultation_charge || 0) +
    parseFloat(formData.medicine_charge || 0) +
    parseFloat(formData.treatment_charge || 0);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await billingAPI.create(formData);
      alert('Bill generated successfully!');
      onSuccess();
    } catch (error) {
      alert('Failed to create bill: ' + error.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

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
        maxWidth: '500px',
        width: '90%'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Generate Bill</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Patient *</label>
            <select
              className="input"
              value={formData.patient_id}
              onChange={(e) => setFormData({ ...formData, patient_id: e.target.value })}
              required
            >
              <option value="">Select Patient</option>
              {patients.map(p => (
                <option key={p.patient_id} value={p.patient_id}>
                  {p.name} ({p.unique_id})
                </option>
              ))}
            </select>
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="label">Bill Date *</label>
            <input
              type="date"
              className="input"
              value={formData.bill_date}
              onChange={(e) => setFormData({ ...formData, bill_date: e.target.value })}
              required
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="label">Consultation Charge (₹)</label>
            <input
              type="number"
              className="input"
              value={formData.consultation_charge}
              onChange={(e) => setFormData({ ...formData, consultation_charge: e.target.value })}
              min="0"
              step="0.01"
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="label">Medicine Charge (₹)</label>
            <input
              type="number"
              className="input"
              value={formData.medicine_charge}
              onChange={(e) => setFormData({ ...formData, medicine_charge: e.target.value })}
              min="0"
              step="0.01"
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="label">Treatment Charge (₹)</label>
            <input
              type="number"
              className="input"
              value={formData.treatment_charge}
              onChange={(e) => setFormData({ ...formData, treatment_charge: e.target.value })}
              min="0"
              step="0.01"
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="label">Payment Mode *</label>
            <select
              className="input"
              value={formData.payment_mode}
              onChange={(e) => setFormData({ ...formData, payment_mode: e.target.value })}
              required
            >
              <option value="cash">Cash</option>
              <option value="card">Card</option>
              <option value="upi">UPI</option>
              <option value="online">Online</option>
            </select>
          </div>

          <div style={{
            padding: '16px',
            background: '#eff6ff',
            borderRadius: '8px',
            marginBottom: '20px'
          }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: '18px', fontWeight: '600' }}>
              <span>Total Amount:</span>
              <span>{formatCurrency(totalAmount)}</span>
            </div>
          </div>

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Generating...' : 'Generate Bill'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

// View Bill Modal
const ViewBillModal = ({ bill, patient, onClose }) => {
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
        maxWidth: '500px',
        width: '90%'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Bill Details</h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <div style={{ display: 'grid', gap: '16px' }}>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Bill Number:</span>
            <p style={{ fontWeight: '600', fontFamily: 'monospace', fontSize: '16px' }}>{bill.bill_number}</p>
          </div>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Patient:</span>
            <p style={{ fontWeight: '500' }}>{patient?.name || 'Unknown'}</p>
          </div>
          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Date:</span>
            <p style={{ fontWeight: '500' }}>{formatDate(bill.bill_date)}</p>
          </div>

          <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>Consultation:</span>
              <span>{formatCurrency(bill.consultation_charge)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>Medicine:</span>
              <span>{formatCurrency(bill.medicine_charge)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '12px' }}>
              <span>Treatment:</span>
              <span>{formatCurrency(bill.treatment_charge)}</span>
            </div>
            <div style={{ 
              display: 'flex', 
              justifyContent: 'space-between',
              padding: '12px',
              background: '#f9fafb',
              borderRadius: '6px',
              fontWeight: '600',
              fontSize: '18px'
            }}>
              <span>Total:</span>
              <span>{formatCurrency(bill.total_amount)}</span>
            </div>
          </div>

          <div style={{ borderTop: '1px solid #e5e7eb', paddingTop: '16px' }}>
            <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '8px' }}>
              <span>Amount Paid:</span>
              <span style={{ color: '#10b981', fontWeight: '600' }}>{formatCurrency(bill.amount_paid)}</span>
            </div>
            <div style={{ display: 'flex', justifyContent: 'space-between' }}>
              <span>Balance:</span>
              <span style={{ color: '#f59e0b', fontWeight: '600' }}>{formatCurrency(bill.balance)}</span>
            </div>
          </div>

          <div>
            <span style={{ color: '#6b7280', fontSize: '14px' }}>Payment Mode:</span>
            <p style={{ fontWeight: '500', textTransform: 'uppercase' }}>{bill.payment_mode}</p>
          </div>
        </div>

        <button onClick={onClose} className="btn btn-primary" style={{ width: '100%', marginTop: '20px' }}>
          Close
        </button>
      </div>
    </div>
  );
};

export default Billing;