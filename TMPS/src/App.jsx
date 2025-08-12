// FIXED: App.jsx with consistent route parameters and proper navigation flow
// src/App.jsx

import React from "react";
import {
  BrowserRouter as Router,
  Routes,
  Route,
  Navigate,
} from "react-router-dom";
import { AuthProvider } from "./context/AuthContext";
import ThemeProvider from "./context/ThemeContext";
import PrivateRoute from "./components/auth/PrivateRoute";
import Layout from "./components/common/Layout";
import { useAuth } from "./hooks/useAuth";

// Auth Pages
import LoginPage from "./pages/auth/LoginPage";
import RegisterPage from "./pages/auth/RegisterPage";
import ForgotPasswordPage from "./pages/auth/ForgotPasswordPage";

// Dashboard Pages
import TrainerDashboardPage from "./pages/trainer/TrainerDashboardPage";
import MentorDashboardPage from "./pages/mentor/MentorDashboardPage";
import StudentDashboardPage from "./pages/student/StudentDashboardPage";

// Trainer Components (keeping existing imports)
import CourseDocumentsList from "./components/trainer/CourseDocuments/CourseDocumentsList";
import AddCourseDocument from "./components/trainer/CourseDocuments/AddCourseDocument";
import ViewCourseDocument from "./components/trainer/CourseDocuments/ViewCourseDocument";
import SessionRecordingsList from "./components/trainer/SessionRecordings/SessionRecordingsList";
import AddSessionRecording from "./components/trainer/SessionRecordings/AddSessionRecording";
import ViewSessionRecording from "./components/trainer/SessionRecordings/ViewSessionRecording";
import TrainerTasksList from "./components/trainer/TrainerTasks/TrainerTasksList";
import AddTrainerTask from "./components/trainer/TrainerTasks/AddTrainerTask";
import ViewTrainerTask from "./components/trainer/TrainerTasks/ViewTrainerTask";
import MockInterviewsList from "./components/trainer/MockInterviews/MockInterviewsList";
import ViewMockInterview from "./components/trainer/MockInterviews/ViewMockInterview";
import DailyStandupsList from "./components/trainer/DailyStandups/DailyStandupsList";
import ViewDailyStandup from "./components/trainer/DailyStandups/ViewDailyStandup";
import MockTestsList from "./components/trainer/MockTests/MockTestsList";
import ViewMockTest from "./components/trainer/MockTests/ViewMockTest";
import StudentResultsList from "./components/trainer/StudentResults/StudentResultsList";
import ViewStudentResults from "./components/trainer/StudentResults/ViewStudentResults";
import SessionsList from "./components/trainer/Sessions/SessionsList";
import ViewSession from "./components/trainer/Sessions/ViewSession";
import AddSession from "./components/trainer/Sessions/AddSession";
import TestCompilationList from "./components/trainer/TestCompilation/TestCompilationList";
import ViewTestCompilation from "./components/trainer/TestCompilation/ViewTestCompilation";

// Mentor Components (keeping existing imports)
import MentorCourseDocumentsList from "./components/mentor/CourseDocuments/CourseDocumentsList";
import MentorAddCourseDocument from "./components/mentor/CourseDocuments/AddCourseDocument";
import MentorViewCourseDocument from "./components/mentor/CourseDocuments/ViewCourseDocument";
import MentorSessionRecordingsList from "./components/mentor/SessionRecordings/SessionRecordingsList";
import MentorAddSessionRecording from "./components/mentor/SessionRecordings/AddSessionRecording";
import MentorViewSessionRecording from "./components/mentor/SessionRecordings/ViewSessionRecording";
import MentorTrainerTasksList from "./components/mentor/TrainerTasks/TrainerTasksList";
import MentorViewTrainerTask from "./components/mentor/TrainerTasks/ViewTrainerTask";
import MentorTaskSubmissionsList from "./components/mentor/TaskSubmissions/TaskSubmissionsList";
import MentorMockInterviewsList from "./components/mentor/MockInterviews/MockInterviewsList";
import MentorViewMockInterview from "./components/mentor/MockInterviews/ViewMockInterview";
import MentorDailyStandupsList from "./components/mentor/DailyStandups/DailyStandupsList";
import MentorViewDailyStandup from "./components/mentor/DailyStandups/ViewDailyStandup";
import MentorMockTestsList from "./components/mentor/MockTests/MockTestsList";
import MentorViewMockTest from "./components/mentor/MockTests/ViewMockTest";
import MentorStudentResultsList from "./components/mentor/StudentResults/StudentResultsList";
import MentorViewStudentResults from "./components/mentor/StudentResults/ViewStudentResults";

// FIXED: Student Mock Interview Components with consistent imports
import StudentCourseDocumentsList from "./components/student/CourseDocuments/CourseDocumentsList";
import StudentViewCourseDocument from "./components/student/CourseDocuments/ViewCourseDocument";
import StudentSessionRecordingsList from "./components/student/SessionRecordings/SessionRecordingsList";
import StudentViewSessionRecording from "./components/student/SessionRecordings/ViewSessionRecording";
import StudentTrainerTasksList from "./components/student/TrainerTasks/TrainerTasksList";
import StudentViewTrainerTask from "./components/student/TrainerTasks/ViewTrainerTask";
import TaskSubmissionsPage from "./components/student/TaskSubmissions/TaskSubmissionsPage";
import StudentAddTaskSubmission from "./components/student/TaskSubmissions/AddTaskSubmission";
import StudentViewTaskSubmission from "./components/student/TaskSubmissions/ViewTaskSubmission";

// FIXED: Mock Interview Components - consistent naming and imports
import StudentMockInterviews from "./components/student/MockInterviews/MockInterviews";
import StartInterview from "./components/student/MockInterviews/StartInterview";
import InterviewResults from "./components/student/MockInterviews/InterviewResultsComponent";

// Daily Standup Components
import Standupcall from "./components/student/DailyStandups/StandupCall";
import StandupCallSession from "./components/student/DailyStandups/StandupCallSession";
import StandupSummary from "./components/student/DailyStandups/StandupSummary";

// Student Mock Test Components
import StudentMockTestsList from "./components/student/MockTest/MockTest";
import MockTestStart from "./components/student/MockTest/MockTestStart";
import DeveloperTest from "./components/student/MockTest/DeveloperTest";
import NonDeveloperTest from "./components/student/MockTest/NonDeveloperTest";
import MockTestResults from "./components/student/MockTest/MockTestResults";

import "./App.css";

// Inline Smart Redirect Component
const SmartRedirect = () => {
  const { user, isAuthenticated } = useAuth();

  console.log("?? SmartRedirect - user:", user);
  console.log("?? SmartRedirect - isAuthenticated:", isAuthenticated);

  // If not authenticated, go to login
  if (!isAuthenticated) {
    console.log("?? SmartRedirect - redirecting to login");
    return <Navigate to="/login" replace />;
  }

  // If authenticated, redirect to their dashboard based on role
  const dashboardPath = `/${user?.role}/dashboard`;
  console.log("?? SmartRedirect - redirecting to:", dashboardPath);
  return <Navigate to={dashboardPath} replace />;
};

function App() {
  console.log("?? App component rendering");

  return (
    <AuthProvider>
      <ThemeProvider>
        <Router>
          <div className="App">
            <Routes>
              {/* Root Route */}
              <Route path="/" element={<SmartRedirect />} />
              
              {/* Public Routes */}
              <Route path="/login" element={<LoginPage />} />
              <Route path="/register" element={<RegisterPage />} />
              <Route path="/forgot-password" element={<ForgotPasswordPage />} />
              
              {/* ==================== TRAINER ROUTES ==================== */}
              <Route
                path="/trainer/dashboard"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <TrainerDashboardPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer"
                element={<Navigate to="/trainer/dashboard" replace />}
              />
              
              {/* Trainer Course Documents Routes */}
              <Route
                path="/trainer/course-documents"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <CourseDocumentsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/course-documents/add"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <AddCourseDocument />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/course-documents/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewCourseDocument />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Session Recordings Routes */}
              <Route
                path="/trainer/session-recordings"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <SessionRecordingsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/session-recordings/add"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <AddSessionRecording />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/session-recordings/view/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewSessionRecording />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Tasks Routes */}
              <Route
                path="/trainer/tasks"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <TrainerTasksList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/tasks/add"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <AddTrainerTask />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/tasks/view/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewTrainerTask />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Sessions Routes */}
              <Route
                path="/trainer/sessions"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <SessionsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/sessions/create"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <AddSession />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/sessions/edit/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <AddSession />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/sessions/view/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewSession />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Mock Interviews Routes */}
              <Route
                path="/trainer/mock-interviews"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <MockInterviewsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/mock-interviews/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewMockInterview />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Daily Standups Routes */}
              <Route
                path="/trainer/daily-standups"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <DailyStandupsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/daily-standups/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewDailyStandup />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Mock Tests Routes */}
              <Route
                path="/trainer/mock-tests"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <MockTestsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/mock-tests/view/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewMockTest />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Student Results Routes */}
              <Route
                path="/trainer/student-results"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <StudentResultsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/student-results/view/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewStudentResults />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Trainer Test Compilation Routes */}
              <Route
                path="/trainer/test-compilation"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <TestCompilationList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/trainer/test-compilation/view/:id"
                element={
                  <PrivateRoute allowedRoles={["trainer"]}>
                    <Layout>
                      <ViewTestCompilation />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* ==================== MENTOR ROUTES ==================== */}
              <Route
                path="/mentor/dashboard"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorDashboardPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor"
                element={<Navigate to="/mentor/dashboard" replace />}
              />
              
              {/* Mentor Course Documents Routes */}
              <Route
                path="/mentor/course-documents"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorCourseDocumentsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/course-documents/add"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorAddCourseDocument />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/course-documents/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewCourseDocument />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Session Recordings Routes */}
              <Route
                path="/mentor/session-recordings"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorSessionRecordingsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/session-recordings/add"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorAddSessionRecording />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/session-recordings/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewSessionRecording />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Tasks Routes */}
              <Route
                path="/mentor/tasks"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorTrainerTasksList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/tasks/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewTrainerTask />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Task Submissions Routes */}
              <Route
                path="/mentor/task-submissions"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorTaskSubmissionsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Student Results Routes */}
              <Route
                path="/mentor/student-results"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorStudentResultsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/student-results/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewStudentResults />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Mock Interviews Routes */}
              <Route
                path="/mentor/mock-interviews"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorMockInterviewsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/mock-interviews/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewMockInterview />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Daily Standups Routes */}
              <Route
                path="/mentor/daily-standups"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorDailyStandupsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/daily-standups/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewDailyStandup />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Mentor Mock Tests Routes */}
              <Route
                path="/mentor/mock-tests"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorMockTestsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/mentor/mock-tests/view/:id"
                element={
                  <PrivateRoute allowedRoles={["mentor"]}>
                    <Layout>
                      <MentorViewMockTest />
                    </Layout>
                  </PrivateRoute>
                }
              />

              {/* ==================== STUDENT ROUTES ==================== */}
              <Route
                path="/student/dashboard"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentDashboardPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student"
                element={<Navigate to="/student/dashboard" replace />}
              />
              
              {/* Student Course Documents Routes */}
              <Route
                path="/student/course-documents"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentCourseDocumentsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/course-documents/view/:id"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentViewCourseDocument />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Student Session Recordings Routes */}
              <Route
                path="/student/session-recordings"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentSessionRecordingsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/session-recordings/view/:id"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentViewSessionRecording />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Student Tasks Routes */}
              <Route
                path="/student/tasks"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentTrainerTasksList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/tasks/view/:id"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentViewTrainerTask />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Student Task Submissions Routes */}
              <Route
                path="/student/task-submissions"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <TaskSubmissionsPage />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/task-submissions/add"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentAddTaskSubmission />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/task-submissions/view/:id"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentViewTaskSubmission />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* FIXED: Student Mock Interviews Routes - Consistent Parameter Naming */}
              <Route
                path="/student/mock-interviews"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentMockInterviews />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* FIXED: Interview Session Route - Using sessionId consistently */}
              <Route
                path="/student/mock-interviews/session/:sessionId"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StartInterview />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* FIXED: Results Route - Using testId consistently */}
              <Route
                path="/student/mock-interviews/results/:testId"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <InterviewResults />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Student Daily Standups Routes */}
              <Route
                path="/student/daily-standups"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <Standupcall />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/daily-standups/call/:testId"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StandupCallSession />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/daily-standups/summary/:testId"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StandupSummary />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* Student Mock Tests Routes */}
              <Route
                path="/student/mock-tests"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <StudentMockTestsList />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/mock-tests/start"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <MockTestStart />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/mock-tests/developer-test"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <DeveloperTest />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/mock-tests/non-developer-test"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <NonDeveloperTest />
                    </Layout>
                  </PrivateRoute>
                }
              />
              <Route
                path="/student/mock-tests/results"
                element={
                  <PrivateRoute allowedRoles={["student"]}>
                    <Layout>
                      <MockTestResults />
                    </Layout>
                  </PrivateRoute>
                }
              />
              
              {/* FIXED: Convenience redirects for better UX */}
              <Route
                path="/student/interviews"
                element={<Navigate to="/student/mock-interviews" replace />}
              />
              <Route
                path="/student/standups"
                element={<Navigate to="/student/daily-standups" replace />}
              />
              <Route
                path="/student/tests"
                element={<Navigate to="/student/mock-tests" replace />}
              />
              <Route
                path="/student/documents"
                element={<Navigate to="/student/course-documents" replace />}
              />
              <Route
                path="/student/recordings"
                element={<Navigate to="/student/session-recordings" replace />}
              />
              <Route
                path="/student/submissions"
                element={<Navigate to="/student/task-submissions" replace />}
              />
              
              {/* FIXED: Fallback routes for interview system */}
              <Route
                path="/student/interview/*"
                element={<Navigate to="/student/mock-interviews" replace />}
              />
              <Route
                path="/weekly_interview/*"
                element={<Navigate to="/student/mock-interviews" replace />}
              />
              
              {/* Catch all route */}
              <Route path="*" element={<Navigate to="/" replace />} />
            </Routes>
          </div>
        </Router>
      </ThemeProvider>
    </AuthProvider>
  );
}

export default App;