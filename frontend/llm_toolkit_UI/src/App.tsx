import styled from 'styled-components';

import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

import Dialog from './components/Dialog.tsx';
import Toolbar from './components/Toolbar.tsx';


const THREAD_UID: string = 'dshdfbk';


const Main = styled.div`
    display: flex;
`;


function App() {
    return (
        <Main>
            <Toolbar threadUID={ THREAD_UID } />
            <Dialog threadUID={ THREAD_UID } />
        </Main>
    )
}

export default App
