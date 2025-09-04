import { useState, useMemo, useEffect } from 'react';
import reactLogo from './assets/react.svg';
import viteLogo from '/vite.svg';
import './App.css';

import DialogService from './services/DialogService.ts';
import Dialog from './components/Dialog.tsx';


const THREAD_UID: string = 'dshdfbk';

function App() {
    const [messages, setMessages] = useState(null);

    useEffect(() => {
        (async () => {
            await Promise.all([
                (async () => setMessages(await DialogService.makeDialog(THREAD_UID)))()
            ])
        })();
    }, []);

    if (messages === null) {
        return <>loading...</>
    }

    return (
        <>
            <Dialog messages={ messages } />
        </>
    )
}

export default App
