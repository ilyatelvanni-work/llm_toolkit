import { useState, useEffect } from 'react';

import styled from 'styled-components';

import MessageModel from '../models/Message.ts';
import DialogService from '../services/DialogService.ts';
import Message from './Message.tsx';


const DialogPanel = styled.div`
`;


export default function({ threadUID }: { threadUID: string }) {
    const [messages, setMessages] = useState(null);

    useEffect(() => {
        (async () => {
            await Promise.all([
                (async () => setMessages(await DialogService.makeDialog(threadUID)))()
            ])
        })();
    }, []);

    if (messages === null) {
        return <DialogPanel>loading...</DialogPanel>
    }

    return <DialogPanel>
        {
            messages.map(msg => <Message key={msg.order} msg={msg} />)
        }
    </DialogPanel>
}
