// import React from 'react';
// import { Box, CircularProgress, Typography } from '@mui/material';

// const LoadingSpinner = ({ message = "Loading..." }) => {
//   return (
//     <Box
//       display="flex"
//       flexDirection="column"
//       justifyContent="center"
//       alignItems="center"
//       minHeight="200px"
//       gap={2}
//     >
//       <CircularProgress size={50} />
//       <Typography variant="body1" color="text.secondary">
//         {message}
//       </Typography>
//     </Box>
//   );
// };

// export default LoadingSpinner;
import React from 'react';
import {
  Box,
  Paper,
  Table,
  TableBody,
  TableCell,
  TableContainer,
  TableHead,
  TableRow,
  Skeleton,
  Typography
} from '@mui/material';

const ShimmerLoader = ({ rows = 5, message = "Loading..." }) => {
  // Create array of shimmer rows
  const shimmerRows = Array.from({ length: rows }, (_, index) => index);

  return (
    <Box>
      {/* Header Shimmer */}
      <Box display="flex" justifyContent="space-between" alignItems="center" mb={3}>
        <Skeleton variant="text" width={200} height={40} />
        <Skeleton variant="rectangular" width={150} height={36} sx={{ borderRadius: 1 }} />
      </Box>

      {/* Filters Shimmer */}
      <Paper sx={{ p: 2, mb: 3 }}>
        <Box display="flex" gap={2} alignItems="center">
          <Skeleton variant="rectangular" width={300} height={40} sx={{ borderRadius: 1 }} />
          <Skeleton variant="rectangular" width={120} height={40} sx={{ borderRadius: 1 }} />
          <Skeleton variant="rectangular" width={120} height={40} sx={{ borderRadius: 1 }} />
        </Box>
      </Paper>

      {/* Table Shimmer */}
      <TableContainer component={Paper}>
        <Table>
          <TableHead>
            <TableRow>
              <TableCell><Skeleton variant="text" width={30} /></TableCell>
              <TableCell><Skeleton variant="text" width={120} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
              <TableCell><Skeleton variant="text" width={60} /></TableCell>
              <TableCell><Skeleton variant="text" width={70} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
              <TableCell><Skeleton variant="text" width={80} /></TableCell>
              <TableCell><Skeleton variant="text" width={80} /></TableCell>
              <TableCell><Skeleton variant="text" width={100} /></TableCell>
            </TableRow>
          </TableHead>
          <TableBody>
            {shimmerRows.map((index) => (
              <TableRow key={index}>
                {/* ID */}
                <TableCell>
                  <Skeleton variant="text" width={20} />
                </TableCell>
                
                {/* Title & Description */}
                <TableCell>
                  <Box>
                    <Skeleton variant="text" width={150} height={20} />
                    <Skeleton variant="text" width={200} height={16} />
                  </Box>
                </TableCell>
                
                {/* Course */}
                <TableCell>
                  <Skeleton variant="text" width={120} />
                </TableCell>
                
                {/* Type */}
                <TableCell>
                  <Skeleton variant="text" width={40} />
                </TableCell>
                
                {/* Size */}
                <TableCell>
                  <Skeleton variant="text" width={60} />
                </TableCell>
                
                {/* Upload Date */}
                <TableCell>
                  <Skeleton variant="text" width={80} />
                </TableCell>
                
                {/* Status */}
                <TableCell>
                  <Skeleton variant="rectangular" width={60} height={24} sx={{ borderRadius: 12 }} />
                </TableCell>
                
                {/* Downloads */}
                <TableCell>
                  <Skeleton variant="text" width={30} />
                </TableCell>
                
                {/* Actions */}
                <TableCell>
                  <Box display="flex" gap={1}>
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                    <Skeleton variant="circular" width={32} height={32} />
                  </Box>
                </TableCell>
              </TableRow>
            ))}
          </TableBody>
        </Table>
      </TableContainer>

      {/* Pagination Shimmer */}
      <Box display="flex" justifyContent="flex-end" mt={2}>
        <Skeleton variant="text" width={200} height={40} />
      </Box>

      {/* Loading Message */}
      {message && (
        <Box display="flex" justifyContent="center" alignItems="center" mt={2}>
          <Typography variant="body2" color="text.secondary">
            {message}
          </Typography>
        </Box>
      )}
    </Box>
  );
};

export default ShimmerLoader;