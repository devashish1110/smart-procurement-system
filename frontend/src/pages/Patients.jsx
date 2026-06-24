import { useState, useEffect } from 'react';
import { patientsAPI } from '../services/api';
import { Users, Plus, Edit, Eye, Search, X } from 'lucide-react';
import { formatDate } from '../utils/helpers';
import Loading from '../components/common/Loading';

const Patients = () => {
  const [patients, setPatients] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState('');
  const [showModal, setShowModal] = useState(false);
  const [selectedPatient, setSelectedPatient] = useState(null);
  const [modalMode, setModalMode] = useState('create');

  useEffect(() => {
    loadPatients();
  }, [search]);

  const loadPatients = async () => {
    try {
      setLoading(true);
      const response = await patientsAPI.getAll({ search, limit: 100 });
      setPatients(response.data);
    } catch (error) {
      console.error('Failed to load patients:', error);
    } finally {
      setLoading(false);
    }
  };

  const handleCreate = () => {
    setSelectedPatient(null);
    setModalMode('create');
    setShowModal(true);
  };

  const handleEdit = (patient) => {
    setSelectedPatient(patient);
    setModalMode('edit');
    setShowModal(true);
  };

  const handleView = (patient) => {
    setSelectedPatient(patient);
    setModalMode('view');
    setShowModal(true);
  };

  if (loading) return <Loading />;

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '24px' }}>
        <div>
          <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
            Patient Management
          </h1>
          <p style={{ color: '#6b7280' }}>
            Manage patient records and information
          </p>
        </div>
        <button onClick={handleCreate} className="btn btn-primary" style={{ gap: '8px' }}>
          <Plus size={20} />
          Add New Patient
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
          <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'start' }}>
            <div>
              <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>
                Total Patients
              </p>
              <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
                {patients.length}
              </h3>
            </div>
            <Users size={24} color="#2563eb" />
          </div>
        </div>
      </div>

      {/* Search */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ position: 'relative' }}>
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
            placeholder="Search patients by name, phone, or ID..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            className="input"
            style={{ paddingLeft: '40px' }}
          />
        </div>
      </div>

      {/* Patients Table */}
      <div className="card" style={{ overflowX: 'auto' }}>
        <table className="table">
          <thead>
            <tr>
              <th>Patient ID</th>
              <th>Name</th>
              <th>Gender</th>
              <th>Phone</th>
              <th>Email</th>
              <th>Date of Birth</th>
              <th>Registered On</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {patients.length === 0 ? (
              <tr>
                <td colSpan="8" style={{ textAlign: 'center', padding: '40px' }}>
                  <p style={{ color: '#6b7280' }}>No patients found</p>
                </td>
              </tr>
            ) : (
              patients.map((patient) => (
                <tr key={patient.patient_id}>
                  <td style={{ fontWeight: '600', fontFamily: 'monospace' }}>
                    {patient.unique_id}
                  </td>
                  <td style={{ fontWeight: '500' }}>{patient.name}</td>
                  <td>{patient.gender || '-'}</td>
                  <td>{patient.phone || '-'}</td>
                  <td style={{ fontSize: '13px' }}>{patient.email || '-'}</td>
                  <td>{formatDate(patient.date_of_birth)}</td>
                  <td>{formatDate(patient.created_at)}</td>
                  <td>
                    <div style={{ display: 'flex', gap: '8px' }}>
                      <button
                        onClick={() => handleView(patient)}
                        className="btn btn-secondary"
                        style={{ padding: '6px 12px', fontSize: '13px' }}
                      >
                        <Eye size={16} />
                      </button>
                      <button
                        onClick={() => handleEdit(patient)}
                        className="btn btn-primary"
                        style={{ padding: '6px 12px', fontSize: '13px' }}
                      >
                        <Edit size={16} />
                      </button>
                    </div>
                  </td>
                </tr>
              ))
            )}
          </tbody>
        </table>
      </div>

      {/* Modal */}
      {showModal && (
        <PatientModal
          patient={selectedPatient}
          mode={modalMode}
          onClose={() => setShowModal(false)}
          onSuccess={() => {
            setShowModal(false);
            loadPatients();
          }}
        />
      )}
    </div>
  );
};

// Patient Modal Component
const PatientModal = ({ patient, mode, onClose, onSuccess }) => {
  const [formData, setFormData] = useState({
    unique_id: patient?.unique_id || '',
    name: patient?.name || '',
    gender: patient?.gender || '',
    phone: patient?.phone || '',
    email: patient?.email || '',
    address: patient?.address || '',
    date_of_birth: patient?.date_of_birth || ''
  });
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    setLoading(true);

    try {
      if (mode === 'create') {
        await patientsAPI.create(formData);
        alert('Patient created successfully!');
      } else if (mode === 'edit') {
        await patientsAPI.update(patient.patient_id, formData);
        alert('Patient updated successfully!');
      }
      onSuccess();
    } catch (error) {
      alert('Operation failed: ' + error.response?.data?.detail);
    } finally {
      setLoading(false);
    }
  };

  const isReadOnly = mode === 'view';

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
        width: '90%',
        maxHeight: '90vh',
        overflowY: 'auto'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '20px' }}>
          <h2 style={{ fontSize: '24px', fontWeight: '700' }}>
            {mode === 'create' ? 'Add New Patient' : mode === 'edit' ? 'Edit Patient' : 'Patient Details'}
          </h2>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer' }}>
            <X size={24} />
          </button>
        </div>

        <form onSubmit={handleSubmit}>
          {/* Unique ID */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Patient ID *</label>
            <input
              type="text"
              className="input"
              value={formData.unique_id}
              onChange={(e) => setFormData({ ...formData, unique_id: e.target.value })}
              required
              disabled={mode === 'edit' || isReadOnly}
              placeholder="e.g., PAT12345"
            />
          </div>

          {/* Name */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Full Name *</label>
            <input
              type="text"
              className="input"
              value={formData.name}
              onChange={(e) => setFormData({ ...formData, name: e.target.value })}
              required
              disabled={isReadOnly}
              placeholder="Enter full name"
            />
          </div>

          {/* Gender */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Gender</label>
            <select
              className="input"
              value={formData.gender}
              onChange={(e) => setFormData({ ...formData, gender: e.target.value })}
              disabled={isReadOnly}
            >
              <option value="">Select Gender</option>
              <option value="M">Male</option>
              <option value="F">Female</option>
            </select>
          </div>

          {/* Phone */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Phone</label>
            <input
              type="tel"
              className="input"
              value={formData.phone}
              onChange={(e) => setFormData({ ...formData, phone: e.target.value })}
              disabled={isReadOnly}
              placeholder="+91XXXXXXXXXX"
            />
          </div>

          {/* Email */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Email</label>
            <input
              type="email"
              className="input"
              value={formData.email}
              onChange={(e) => setFormData({ ...formData, email: e.target.value })}
              disabled={isReadOnly}
              placeholder="email@example.com"
            />
          </div>

          {/* Date of Birth */}
          <div style={{ marginBottom: '16px' }}>
            <label className="label">Date of Birth</label>
            <input
              type="date"
              className="input"
              value={formData.date_of_birth}
              onChange={(e) => setFormData({ ...formData, date_of_birth: e.target.value })}
              disabled={isReadOnly}
            />
          </div>

          {/* Address */}
          <div style={{ marginBottom: '20px' }}>
            <label className="label">Address</label>
            <textarea
              className="input"
              rows="3"
              value={formData.address}
              onChange={(e) => setFormData({ ...formData, address: e.target.value })}
              disabled={isReadOnly}
              placeholder="Enter full address"
            />
          </div>

          {/* Actions */}
          <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
            <button type="button" onClick={onClose} className="btn btn-secondary">
              {isReadOnly ? 'Close' : 'Cancel'}
            </button>
            {!isReadOnly && (
              <button type="submit" className="btn btn-primary" disabled={loading}>
                {loading ? 'Saving...' : mode === 'create' ? 'Create Patient' : 'Update Patient'}
              </button>
            )}
          </div>
        </form>
      </div>
    </div>
  );
};

export default Patients;