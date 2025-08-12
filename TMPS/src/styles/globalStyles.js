import { createTheme } from '@mui/material/styles';

export const globalStyles = {
  // Layout styles
  layout: {
    minHeight: '100vh',
    display: 'flex',
    flexDirection: 'column',
  },
  
  main: {
    flexGrow: 1,
    padding: 3,
    marginTop: '64px', // AppBar height
    marginLeft: '240px', // Sidebar width
    transition: 'margin-left 0.3s ease',
    '@media (max-width: 768px)': {
      marginLeft: 0,
      padding: 2,
    },
  },

  mainCollapsed: {
    marginLeft: '60px', // Collapsed sidebar width
    '@media (max-width: 768px)': {
      marginLeft: 0,
    },
  },

  // Sidebar styles
  sidebar: {
    width: '240px',
    flexShrink: 0,
    '& .MuiDrawer-paper': {
      width: '240px',
      boxSizing: 'border-box',
      marginTop: '64px', // AppBar height
      height: 'calc(100vh - 64px)',
    },
  },

  sidebarCollapsed: {
    width: '60px',
    '& .MuiDrawer-paper': {
      width: '60px',
    },
  },

  // Header styles
  header: {
    zIndex: 1201, // Above sidebar
    '& .MuiToolbar-root': {
      paddingLeft: 3,
      paddingRight: 3,
    },
  },

  // Card styles
  card: {
    marginBottom: 2,
    '& .MuiCardHeader-root': {
      paddingBottom: 1,
    },
    '& .MuiCardContent-root': {
      paddingTop: 1,
      '&:last-child': {
        paddingBottom: 2,
      },
    },
  },

  // Form styles
  form: {
    '& .MuiTextField-root': {
      marginBottom: 2,
    },
    '& .MuiButton-root': {
      marginTop: 2,
      marginRight: 1,
    },
  },

  // Table styles
  table: {
    '& .MuiTableHead-root': {
      '& .MuiTableCell-root': {
        fontWeight: 600,
        backgroundColor: 'rgba(0, 0, 0, 0.04)',
      },
    },
    '& .MuiTableBody-root': {
      '& .MuiTableRow-root': {
        '&:hover': {
          backgroundColor: 'rgba(0, 0, 0, 0.04)',
        },
      },
    },
  },

  // Dashboard styles
  dashboard: {
    '& .dashboard-cards': {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(250px, 1fr))',
      gap: 2,
      marginBottom: 3,
    },
    '& .dashboard-charts': {
      display: 'grid',
      gridTemplateColumns: 'repeat(auto-fit, minmax(400px, 1fr))',
      gap: 2,
    },
  },

  // Status badges
  statusBadge: {
    padding: '4px 8px',
    borderRadius: '12px',
    fontSize: '0.75rem',
    fontWeight: 500,
    textTransform: 'uppercase',
  },

  statusSuccess: {
    backgroundColor: '#e8f5e8',
    color: '#2e7d32',
  },

  statusWarning: {
    backgroundColor: '#fff3e0',
    color: '#ed6c02',
  },

  statusError: {
    backgroundColor: '#ffeaea',
    color: '#d32f2f',
  },

  statusInfo: {
    backgroundColor: '#e3f2fd',
    color: '#0288d1',
  },

  // Loading styles
  loading: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
    height: '200px',
  },

  // Error styles
  error: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: 3,
    textAlign: 'center',
    '& .error-icon': {
      fontSize: '4rem',
      color: '#d32f2f',
      marginBottom: 2,
    },
    '& .error-message': {
      marginBottom: 2,
    },
  },

  // Empty state styles
  empty: {
    display: 'flex',
    flexDirection: 'column',
    alignItems: 'center',
    padding: 4,
    textAlign: 'center',
    '& .empty-icon': {
      fontSize: '4rem',
      color: '#757575',
      marginBottom: 2,
    },
    '& .empty-message': {
      marginBottom: 2,
    },
  },

  // Animation utilities
  fadeIn: {
    animation: 'fadeIn 0.3s ease-in-out',
    '@keyframes fadeIn': {
      from: { opacity: 0 },
      to: { opacity: 1 },
    },
  },

  slideIn: {
    animation: 'slideIn 0.3s ease-in-out',
    '@keyframes slideIn': {
      from: { transform: 'translateY(-20px)', opacity: 0 },
      to: { transform: 'translateY(0)', opacity: 1 },
    },
  },

  // Utility classes
  fullWidth: {
    width: '100%',
  },

  centered: {
    display: 'flex',
    justifyContent: 'center',
    alignItems: 'center',
  },

  spaceBetween: {
    display: 'flex',
    justifyContent: 'space-between',
    alignItems: 'center',
  },

  spaceAround: {
    display: 'flex',
    justifyContent: 'space-around',
    alignItems: 'center',
  },

  flexStart: {
    display: 'flex',
    justifyContent: 'flex-start',
    alignItems: 'center',
  },

  flexEnd: {
    display: 'flex',
    justifyContent: 'flex-end',
    alignItems: 'center',
  },

  // Responsive utilities
  hideOnMobile: {
    '@media (max-width: 768px)': {
      display: 'none',
    },
  },

  showOnMobile: {
    display: 'none',
    '@media (max-width: 768px)': {
      display: 'block',
    },
  },

  // Scroll styles
  scrollable: {
    overflow: 'auto',
    '&::-webkit-scrollbar': {
      width: '6px',
    },
    '&::-webkit-scrollbar-track': {
      background: '#f1f1f1',
      borderRadius: '3px',
    },
    '&::-webkit-scrollbar-thumb': {
      background: '#c1c1c1',
      borderRadius: '3px',
      '&:hover': {
        background: '#a8a8a8',
      },
    },
  },

  // Paper elevation variants
  elevation1: {
    boxShadow: '0 1px 3px rgba(0,0,0,0.12), 0 1px 2px rgba(0,0,0,0.24)',
  },

  elevation2: {
    boxShadow: '0 3px 6px rgba(0,0,0,0.16), 0 3px 6px rgba(0,0,0,0.23)',
  },

  elevation3: {
    boxShadow: '0 10px 20px rgba(0,0,0,0.19), 0 6px 6px rgba(0,0,0,0.23)',
  },
};

export default globalStyles;