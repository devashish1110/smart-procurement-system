import { useState, useEffect } from 'react';
import { reportsAPI } from '../services/api';
import { TrendingUp, Download, Calendar } from 'lucide-react';
import { formatCurrency, formatDate } from '../utils/helpers';
import { LineChart, Line, BarChart, Bar, PieChart, Pie, Cell, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import Loading from '../components/common/Loading';

const Reports = () => {
  const [reportType, setReportType] = useState('financial');
  const [dateRange, setDateRange] = useState({
    start_date: new Date(new Date().setDate(new Date().getDate() - 30)).toISOString().split('T')[0],
    end_date: new Date().toISOString().split('T')[0]
  });
  const [reportData, setReportData] = useState(null);
  const [loading, setLoading] = useState(false);

  useEffect(() => {
    loadReport();
  }, [reportType, dateRange]);

  const loadReport = async () => {
    try {
      setLoading(true);
      let response;
      
      if (reportType === 'financial') {
        response = await reportsAPI.getFinancial(dateRange);
      } else if (reportType === 'inventory') {
        response = await reportsAPI.getInventory();
      } else if (reportType === 'patient-visits') {
        response = await reportsAPI.getPatientVisits(dateRange);
      } else if (reportType === 'procurement') {
        response = await reportsAPI.getProcurement(dateRange);
      }
      
      setReportData(response.data);
    } catch (error) {
      console.error('Failed to load report:', error);
    } finally {
      setLoading(false);
    }
  };

  const COLORS = ['#2563eb', '#10b981', '#f59e0b', '#ef4444', '#8b5cf6'];

  return (
    <div style={{ padding: '24px' }}>
      {/* Header */}
      <div style={{ marginBottom: '24px' }}>
        <h1 style={{ fontSize: '28px', fontWeight: '700', marginBottom: '8px' }}>
          Reports & Analytics
        </h1>
        <p style={{ color: '#6b7280' }}>
          View financial reports and business analytics
        </p>
      </div>

      {/* Controls */}
      <div className="card" style={{ marginBottom: '24px' }}>
        <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap', alignItems: 'end' }}>
          {/* Report Type */}
          <div style={{ flex: '1', minWidth: '200px' }}>
            <label className="label">Report Type</label>
            <select
              className="input"
              value={reportType}
              onChange={(e) => setReportType(e.target.value)}
            >
              <option value="financial">Financial Report</option>
              <option value="inventory">Inventory Report</option>
              <option value="patient-visits">Patient Visits</option>
              <option value="procurement">Procurement Report</option>
            </select>
          </div>

          {/* Date Range */}
          {reportType !== 'inventory' && (
            <>
              <div style={{ flex: '1', minWidth: '150px' }}>
                <label className="label">Start Date</label>
                <input
                  type="date"
                  className="input"
                  value={dateRange.start_date}
                  onChange={(e) => setDateRange({ ...dateRange, start_date: e.target.value })}
                />
              </div>
              <div style={{ flex: '1', minWidth: '150px' }}>
                <label className="label">End Date</label>
                <input
                  type="date"
                  className="input"
                  value={dateRange.end_date}
                  onChange={(e) => setDateRange({ ...dateRange, end_date: e.target.value })}
                />
              </div>
            </>
          )}

          {/* Generate Button */}
          <button
            onClick={loadReport}
            className="btn btn-primary"
            style={{ gap: '8px' }}
          >
            <TrendingUp size={18} />
            Generate Report
          </button>
        </div>
      </div>

      {/* Report Content */}
      {loading ? (
        <Loading />
      ) : reportData ? (
        <>
          {reportType === 'financial' && <FinancialReport data={reportData} />}
          {reportType === 'inventory' && <InventoryReport data={reportData} />}
          {reportType === 'patient-visits' && <PatientVisitsReport data={reportData} />}
          {reportType === 'procurement' && <ProcurementReport data={reportData} />}
        </>
      ) : (
        <div className="card">
          <p style={{ textAlign: 'center', color: '#6b7280', padding: '40px' }}>
            Select report type and date range, then click Generate Report
          </p>
        </div>
      )}
    </div>
  );
};

// Financial Report Component
const FinancialReport = ({ data }) => {
  const pieData = [
    { name: 'Consultation', value: data.revenue?.breakdown?.consultation || 0 },
    { name: 'Medicine', value: data.revenue?.breakdown?.medicine || 0 },
    { name: 'Treatment', value: data.revenue?.breakdown?.treatment || 0 }
  ];

  const COLORS = ['#2563eb', '#10b981', '#f59e0b'];

  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      {/* Summary Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))', gap: '16px' }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Billed</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#2563eb' }}>
            {formatCurrency(data.revenue?.total_billed || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Collected</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#10b981' }}>
            {formatCurrency(data.revenue?.total_collected || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Outstanding</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
            {formatCurrency(data.revenue?.outstanding || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Gross Profit</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#10b981' }}>
            {formatCurrency(data.profit?.gross_profit || 0)}
          </h3>
        </div>
      </div>

      {/* Charts */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))', gap: '24px' }}>
        {/* Revenue Breakdown Pie Chart */}
        <div className="card">
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Revenue Breakdown</h3>
          <ResponsiveContainer width="100%" height={300}>
            <PieChart>
              <Pie
                data={pieData}
                cx="50%"
                cy="50%"
                labelLine={false}
                label={(entry) => `${entry.name}: ${formatCurrency(entry.value)}`}
                outerRadius={80}
                fill="#8884d8"
                dataKey="value"
              >
                {pieData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
                ))}
              </Pie>
              <Tooltip formatter={(value) => formatCurrency(value)} />
            </PieChart>
          </ResponsiveContainer>
        </div>

        {/* Daily Revenue Trend */}
        {data.daily_trend && data.daily_trend.length > 0 && (
          <div className="card">
            <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Daily Revenue Trend</h3>
            <ResponsiveContainer width="100%" height={300}>
              <LineChart data={data.daily_trend}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="date" />
                <YAxis />
                <Tooltip formatter={(value) => formatCurrency(value)} />
                <Legend />
                <Line type="monotone" dataKey="revenue" stroke="#2563eb" strokeWidth={2} />
              </LineChart>
            </ResponsiveContainer>
          </div>
        )}
      </div>
    </div>
  );
};

// Inventory Report Component
const InventoryReport = ({ data }) => {
  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Medicines</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {data.summary?.total_medicines || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Value</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#10b981' }}>
            {formatCurrency(data.summary?.total_inventory_value || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Low Stock Items</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#f59e0b' }}>
            {data.summary?.low_stock_items || 0}
          </h3>
        </div>
      </div>

      {/* Top Items by Value */}
      <div className="card">
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Top Items by Stock Value</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Medicine Name</th>
              <th>Category</th>
              <th>Current Stock</th>
              <th>Stock Value</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody>
            {data.inventory?.slice(0, 10).map((item, index) => (
              <tr key={index}>
                <td style={{ fontWeight: '500' }}>{item.medicine_name}</td>
                <td>{item.category || '-'}</td>
                <td>{item.current_stock}</td>
                <td style={{ fontWeight: '600' }}>{formatCurrency(item.stock_value)}</td>
                <td>
                  <span className={`badge ${item.status === 'adequate' ? 'badge-success' : 'badge-warning'}`}>
                    {item.status}
                  </span>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

// Patient Visits Report Component
const PatientVisitsReport = ({ data }) => {
  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Visits</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {data.summary?.total_visits || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Unique Patients</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {data.summary?.unique_patients || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Avg Visits/Day</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {data.summary?.average_visits_per_day?.toFixed(1) || 0}
          </h3>
        </div>
      </div>

      {/* Daily Trend */}
      {data.daily_trend && data.daily_trend.length > 0 && (
        <div className="card">
          <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Daily Visit Trend</h3>
          <ResponsiveContainer width="100%" height={300}>
            <BarChart data={data.daily_trend}>
              <CartesianGrid strokeDasharray="3 3" />
              <XAxis dataKey="date" />
              <YAxis />
              <Tooltip />
              <Legend />
              <Bar dataKey="visits" fill="#2563eb" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
};

// Procurement Report Component
const ProcurementReport = ({ data }) => {
  return (
    <div style={{ display: 'grid', gap: '24px' }}>
      {/* Summary */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(auto-fit, minmax(200px, 1fr))', gap: '16px' }}>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total POs</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {data.summary?.total_purchase_orders || 0}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Total Spending</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700', color: '#2563eb' }}>
            {formatCurrency(data.summary?.total_spending || 0)}
          </h3>
        </div>
        <div className="card">
          <p style={{ fontSize: '14px', color: '#6b7280', marginBottom: '8px' }}>Avg PO Value</p>
          <h3 style={{ fontSize: '28px', fontWeight: '700' }}>
            {formatCurrency(data.summary?.average_po_value || 0)}
          </h3>
        </div>
      </div>

      {/* Top Vendors */}
      <div className="card">
        <h3 style={{ fontSize: '18px', fontWeight: '600', marginBottom: '16px' }}>Top Vendors by Spending</h3>
        <table className="table">
          <thead>
            <tr>
              <th>Vendor Name</th>
              <th>Order Count</th>
              <th>Total Spent</th>
            </tr>
          </thead>
          <tbody>
            {data.top_vendors?.map((vendor, index) => (
              <tr key={index}>
                <td style={{ fontWeight: '500' }}>{vendor.vendor_name}</td>
                <td>{vendor.order_count}</td>
                <td style={{ fontWeight: '600' }}>{formatCurrency(vendor.total_spent)}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </div>
  );
};

export default Reports;