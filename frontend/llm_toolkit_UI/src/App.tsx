import styled from 'styled-components';

import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

import { DialogContextProvider } from './context/Dialog.tsx';
import Dialog from './components/Dialog.tsx';
import Toolbar from './components/Toolbar.tsx';


const THREAD_UID: string = 'dshdfbk';


const Main = styled.div`
    display: flex;
    height: 100vh;
    overflow: hidden;
`;


function App() {
    return (
        <Main>
            <DialogContextProvider>
                <Toolbar threadUID={ THREAD_UID } />
                <Dialog threadUID={ THREAD_UID } />
            </DialogContextProvider>
        </Main>
    )
}

export default App
