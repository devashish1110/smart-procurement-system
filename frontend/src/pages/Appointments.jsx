import { useState, useEffect } from 'react';
import { appointmentsAPI, patientsAPI } from '../services/api';
import { Calendar, Plus, CheckCircle, X } from 'lucide-react';
import { formatDate, getStatusColor } from '../utils/helpers';
import Loading from '../components/common/Loading';

const Appointments = () => {
  const [appointments, setAppointments] = useState([]);
  const [patients, setPatients] = useState([]);
  const [stats, setStats] = useState(null);
  const [loading, setLoading] = useState(true);
  const [filter, setFilter] = useState('all');
  const [showModal, setShowModal] = useState(false);

  useEffect(() => {
    loadData();
  }, [filter]);

  const loadData = async () => {
    try {
      setLoading(true);
      const params = {};
      if (filter === 'today') {
        params.appointment_date = new Date().toISOString().split('T')[0];
      }

      const [appointmentsRes, patientsRes, statsRes] = await Promise.all([
        appointmentsAPI.getAll(params),
        patientsAPI.getAll({ limit: 1000 }),
        appointmentsAPI.getStats()
      ]);

      setAppointments(appointmentsRes.data);
      setPatients(patientsRes.data);
      setStats(statsRes.data);
    } catch (error) {
      console.error('Failed to load data:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleStatusChange = async (appointmentId, newStatus) => {
    if (!window.confirm(`Change status to ${newStatus}?`)) return;

    try {
      await appointmentsAPI.updateStatus(appointmentId, newStatus);
      alert('Status updated successfully!');
      loadData();
    } catch (error) {
      alert('Failed to update status: ' + error.response?.data?.detail);
    }
  };

  if (loading) return <Loading />;

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
            Appointments
          </h1>
          <p style={{ color: '#6b7280' }}>
            Schedule and manage patient appointments
          </p>
        </div>
        <button onClick={() => setShowModal(true)} className="btn btn-primary" style={{ gap: '8px' }}>
          <Plus size={20} />
          Schedule Appointment
        </button>
      </div>

      {/* Stats */}
      <div style={{
        display: 'grid',
        gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))',
        gap: '16px',
        marginBottom: '24px'
      }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Today's Appointments
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {stats?.todays_appointments || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
            Upcoming (7 days)
          </p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {stats?.upcoming_appointments || 0}
          </h3>
        </div>
      </div>

      {/* Filters */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '8px' }}>
          {['all', 'today', 'scheduled', 'completed'].map(f => (
            <button
              key={f}
              onClick={() => setFilter(f)}
              style={{
                padding: '8px 16px',
                background: filter === f ? '#2563eb' : '#f3f4f6',
                color: filter === f ? 'white' : '#6b7280',
                border: 'none',
                borderRadius: '6px',
                cursor: 'pointer',
                fontSize: '14px',
                fontWeight: '500',
                textTransform: 'capitalize'
              }}
            >
              {f}
            </button>
          ))}
        </div>
      </div>

      {/* Appointments Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Date</th>
              <th>Time Slot</th>
              <th>Patient</th>
              <th>Treatment</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {appointments.length === 0 ? (
              <tr>
                <td colSpan="6" style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#6b7280' }}>No appointments found</p>
                </td>
              </tr>
            ) : (
              appointments.map((apt) => {
                const patient = patients.find(p => p.patient_id === apt.patient_id);
                return (
                  <tr key={apt.appointment_id}>
                    <td style={{ fontWeight: '500' }}>{formatDate(apt.appointment_date)}</td>
                    <td>
                      <span className="badge badge-info">
                        {apt.time_slot === 'M' ? 'Morning' : 'Evening'}
                      </span>
                    </td>
                    <td>{patient?.name || 'Unknown'}</td>
                    <td>{apt.treatment_id || '-'}</td>
                    <td>
                      <span className={`badge ${getStatusColor(apt.status)}`}>
                        {apt.status}
                      </span>
                    </td>
                    <td>
                      <div style={{ display: 'flex', gap: '8px' }}>
                        {apt.status === 'scheduled' && (
                          <button
                            onClick={() => handleStatusChange(apt.appointment_id, 'completed')}
                            className="btn btn-success"
                            style={{ padding: '6px 12px', fontSize: '13px' }}
                          >
                            <CheckCircle size={16} />
                          </button>
                        )}
                      </div>
                    </td>
                  </tr>
                );
              })
            )}
          </tbody>
        </table>
      </div>

      {/* Create Modal */}
      {showModal && (
        <CreateAppointmentModal
          patients={patients}
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            loadData();
          }}
        />
      )}
    </div>
  );
};

// Create Appointment Modal
const CreateAppointmentModal = ({ patients, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    patient_id: '',
    appointment_date: '',
    time_slot: '',
    notes: ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      await appointmentsAPI.create(formData);
      alert('Appointment scheduled successfully!');
      onSuccess();
    } catch (error) {
      alert('Failed to create appointment: ' + error.response?.data?.detail);
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
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>Schedule Appointment</h2>
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
            <label className="label">Appointment Date *</label>
            <input
              type="date"
              className="input"
              value={formData.appointment_date}
              onChange={(e) => setFormData({ ...formData, appointment_date: e.target.value })}
              required
              min={new Date().toISOString().split('T')[0]}
            />
          </div>

          <div style={{ marginBottom: '16px' }}>
            <label className="label">Time Slot *</label>
            <select
              className="input"
              value={formData.time_slot}
              onChange={(e) => setFormData({ ...formData, time_slot: e.target.value })}
              required
            >
              <option value="">Select Time Slot</option>
              <option value="M">Morning</option>
              <option value="E">Evening</option>
            </select>
          </div>

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

          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              Cancel
            </button>
            <button type="submit" className="btn btn-primary" disabled={loading}>
              {loading ? 'Scheduling...' : 'Schedule Appointment'}
            </button>
          </div>
        </form>
      </div>
    </div>
  );
};

export default Appointments;