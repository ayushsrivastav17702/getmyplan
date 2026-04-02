import {
  Chart as ChartJS,
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler,
} from 'chart.js';
import { Line, Bar, Pie, Doughnut } from 'react-chartjs-2';

// Register Chart.js components
ChartJS.register(
  CategoryScale,
  LinearScale,
  PointElement,
  LineElement,
  BarElement,
  ArcElement,
  Title,
  Tooltip,
  Legend,
  Filler
);

// Salesforce color palette
const SF_COLORS = {
  primary: '#0176D3',
  primaryLight: '#1B96FF',
  success: '#2E844A',
  warning: '#DD7A01',
  error: '#EA001E',
  neutral: '#706E6B',
  slate: '#64748B',
  colors: [
    '#0176D3', '#2E844A', '#DD7A01', '#EA001E', '#706E6B',
    '#1B96FF', '#45C65A', '#FE9339', '#FF5D2D', '#939393'
  ]
};

// Common chart options
const commonOptions = {
  responsive: true,
  maintainAspectRatio: false,
  plugins: {
    legend: {
      position: 'bottom',
      labels: {
        font: {
          family: "'IBM Plex Sans', sans-serif",
          size: 12
        },
        padding: 16,
        usePointStyle: true,
        pointStyle: 'circle'
      }
    },
    tooltip: {
      backgroundColor: '#0F172A',
      titleFont: {
        family: "'IBM Plex Sans', sans-serif",
        size: 13,
        weight: '600'
      },
      bodyFont: {
        family: "'IBM Plex Sans', sans-serif",
        size: 12
      },
      padding: 12,
      cornerRadius: 4
    }
  }
};

// Line Chart Component
export const LineChart = ({ 
  data, 
  labels, 
  datasets, 
  title = '',
  showLegend = true,
  height = 300,
  formatValue = (v) => v
}) => {
  const chartData = {
    labels,
    datasets: datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      borderColor: ds.color || SF_COLORS.colors[i % SF_COLORS.colors.length],
      backgroundColor: ds.fill 
        ? `${ds.color || SF_COLORS.colors[i % SF_COLORS.colors.length]}20`
        : 'transparent',
      borderWidth: 2,
      fill: ds.fill || false,
      tension: 0.3,
      pointRadius: 4,
      pointHoverRadius: 6
    }))
  };

  const options = {
    ...commonOptions,
    plugins: {
      ...commonOptions.plugins,
      legend: {
        ...commonOptions.plugins.legend,
        display: showLegend
      },
      title: {
        display: !!title,
        text: title,
        font: {
          family: "'Chivo', sans-serif",
          size: 16,
          weight: '600'
        },
        padding: { bottom: 16 }
      },
      tooltip: {
        ...commonOptions.plugins.tooltip,
        callbacks: {
          label: (context) => `${context.dataset.label}: ${formatValue(context.raw)}`
        }
      }
    },
    scales: {
      x: {
        grid: { display: false },
        ticks: {
          font: { family: "'IBM Plex Sans', sans-serif", size: 11 }
        }
      },
      y: {
        grid: { color: '#E2E8F0' },
        ticks: {
          font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
          callback: formatValue
        }
      }
    }
  };

  return (
    <div style={{ height }}>
      <Line data={chartData} options={options} />
    </div>
  );
};

// Bar Chart Component
export const BarChart = ({ 
  data, 
  labels, 
  datasets, 
  title = '',
  horizontal = false,
  showLegend = true,
  height = 300,
  formatValue = (v) => v
}) => {
  const chartData = {
    labels,
    datasets: datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: ds.colors || ds.color || SF_COLORS.colors[i % SF_COLORS.colors.length],
      borderColor: ds.borderColor || 'transparent',
      borderWidth: ds.borderWidth || 0,
      borderRadius: 4,
      barThickness: ds.barThickness || 'flex',
      maxBarThickness: 40
    }))
  };

  const options = {
    ...commonOptions,
    indexAxis: horizontal ? 'y' : 'x',
    plugins: {
      ...commonOptions.plugins,
      legend: {
        ...commonOptions.plugins.legend,
        display: showLegend && datasets.length > 1
      },
      title: {
        display: !!title,
        text: title,
        font: {
          family: "'Chivo', sans-serif",
          size: 16,
          weight: '600'
        },
        padding: { bottom: 16 }
      },
      tooltip: {
        ...commonOptions.plugins.tooltip,
        callbacks: {
          label: (context) => `${context.dataset.label || ''}: ${formatValue(context.raw)}`
        }
      }
    },
    scales: {
      x: {
        grid: { display: horizontal },
        ticks: {
          font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
          callback: horizontal ? formatValue : undefined
        }
      },
      y: {
        grid: { display: !horizontal, color: '#E2E8F0' },
        ticks: {
          font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
          callback: !horizontal ? formatValue : undefined
        }
      }
    }
  };

  return (
    <div style={{ height }}>
      <Bar data={chartData} options={options} />
    </div>
  );
};

// Doughnut/Pie Chart Component
export const DoughnutChart = ({ 
  data, 
  labels, 
  title = '',
  showLegend = true,
  height = 300,
  formatValue = (v) => v,
  isPie = false
}) => {
  const chartData = {
    labels,
    datasets: [{
      data,
      backgroundColor: SF_COLORS.colors.slice(0, data.length),
      borderColor: '#fff',
      borderWidth: 2
    }]
  };

  const options = {
    ...commonOptions,
    cutout: isPie ? 0 : '60%',
    plugins: {
      ...commonOptions.plugins,
      legend: {
        ...commonOptions.plugins.legend,
        display: showLegend,
        position: 'right'
      },
      title: {
        display: !!title,
        text: title,
        font: {
          family: "'Chivo', sans-serif",
          size: 16,
          weight: '600'
        },
        padding: { bottom: 16 }
      },
      tooltip: {
        ...commonOptions.plugins.tooltip,
        callbacks: {
          label: (context) => {
            const total = context.dataset.data.reduce((a, b) => a + b, 0);
            const percentage = ((context.raw / total) * 100).toFixed(1);
            return `${context.label}: ${formatValue(context.raw)} (${percentage}%)`;
          }
        }
      }
    }
  };

  const ChartComponent = isPie ? Pie : Doughnut;

  return (
    <div style={{ height }}>
      <ChartComponent data={chartData} options={options} />
    </div>
  );
};

// Area Chart (Line with fill)
export const AreaChart = ({ 
  data, 
  labels, 
  datasets, 
  title = '',
  showLegend = true,
  height = 300,
  formatValue = (v) => v
}) => {
  return (
    <LineChart
      data={data}
      labels={labels}
      datasets={datasets.map(ds => ({ ...ds, fill: true }))}
      title={title}
      showLegend={showLegend}
      height={height}
      formatValue={formatValue}
    />
  );
};

// Stacked Bar Chart
export const StackedBarChart = ({ 
  data, 
  labels, 
  datasets, 
  title = '',
  horizontal = false,
  showLegend = true,
  height = 300,
  formatValue = (v) => v
}) => {
  const chartData = {
    labels,
    datasets: datasets.map((ds, i) => ({
      label: ds.label,
      data: ds.data,
      backgroundColor: ds.color || SF_COLORS.colors[i % SF_COLORS.colors.length],
      borderRadius: 4
    }))
  };

  const options = {
    ...commonOptions,
    indexAxis: horizontal ? 'y' : 'x',
    plugins: {
      ...commonOptions.plugins,
      legend: {
        ...commonOptions.plugins.legend,
        display: showLegend
      },
      title: {
        display: !!title,
        text: title,
        font: {
          family: "'Chivo', sans-serif",
          size: 16,
          weight: '600'
        },
        padding: { bottom: 16 }
      }
    },
    scales: {
      x: {
        stacked: true,
        grid: { display: horizontal },
        ticks: {
          font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
          callback: horizontal ? formatValue : undefined
        }
      },
      y: {
        stacked: true,
        grid: { display: !horizontal, color: '#E2E8F0' },
        ticks: {
          font: { family: "'IBM Plex Sans', sans-serif", size: 11 },
          callback: !horizontal ? formatValue : undefined
        }
      }
    }
  };

  return (
    <div style={{ height }}>
      <Bar data={chartData} options={options} />
    </div>
  );
};

export default {
  LineChart,
  BarChart,
  DoughnutChart,
  AreaChart,
  StackedBarChart,
  SF_COLORS
};
