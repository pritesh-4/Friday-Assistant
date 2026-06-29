import { Routes, Route } from 'react-router-dom'
import Navbar from './components/Navbar'
import Footer from './components/Footer'
import Home from './pages/Home'
import Chat from './pages/Chat'

const App = () => {
  return (
    <div>
      <Routes>
        <Route path='/' element={<><Navbar/><Home/><Footer/></>}/>
        <Route path='/chat' element={<Chat/>}/>
      </Routes>
    </div>
  )
}

export default App