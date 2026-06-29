import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Chat from './pages/Chat'
import Vision from './pages/Vision'
import About from './pages/About'

const App = () => {
  return (
    <div>
      <Routes>
        <Route path='/' element={<><Navbar/><Home/><Footer/></>}/>
        <Route path='/chat' element={<Chat/>}/>
        <Route path='/vision' element={<><Navbar/><Vision/><Footer/></>}/>
        <Route path='/about' element={<><Navbar/><About/><Footer/></>}/>
      </Routes>
    </div>
  )
}

export default App