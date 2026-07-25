import { Routes, Route, useLocation } from 'react-router-dom'
import { AnimatePresence, motion } from 'framer-motion'
import React, { Suspense } from 'react';
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Chat from './pages/Chat'

const Vision = React.lazy(() => import('./pages/Vision'));
const About = React.lazy(() => import('./pages/About'));
const Planning = React.lazy(() => import('./pages/Planning'));
const BackgroundOps = React.lazy(() => import('./pages/BackgroundOps'));

// A wrapper to animate page transitions
const PageWrapper = ({ children }) => (
  <motion.div
    initial={{ opacity: 0, y: 10 }}
    animate={{ opacity: 1, y: 0 }}
    exit={{ opacity: 0, y: -10 }}
    transition={{ duration: 0.4, ease: "easeInOut" }}
    className="w-full h-full"
  >
    {children}
  </motion.div>
);

const App = () => {
  const location = useLocation();
  return (
    <div className="app-container">
      <AnimatePresence mode="wait">
        <Routes location={location} key={location.pathname}>
          <Route path='/' element={<PageWrapper><Navbar/><Home/><Footer/></PageWrapper>}/>
          <Route path='/chat' element={<PageWrapper><Chat/></PageWrapper>}/>
          <Route path='/vision' element={<PageWrapper><Navbar/><Suspense fallback={<div>Loading Vision...</div>}><Vision/></Suspense><Footer/></PageWrapper>}/>
          <Route path='/planning' element={<PageWrapper><Navbar/><Suspense fallback={<div>Loading Planning...</div>}><Planning/></Suspense><Footer/></PageWrapper>}/>
          <Route path='/background' element={<PageWrapper><Navbar/><Suspense fallback={<div>Loading Background Ops...</div>}><BackgroundOps/></Suspense><Footer/></PageWrapper>}/>
          <Route path='/about' element={<PageWrapper><Navbar/><Suspense fallback={<div>Loading About...</div>}><About/></Suspense><Footer/></PageWrapper>}/>
        </Routes>
      </AnimatePresence>
    </div>
  )
}

export default App