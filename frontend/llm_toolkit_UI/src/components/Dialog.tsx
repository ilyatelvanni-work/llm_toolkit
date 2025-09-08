import { useState, useEffect } from 'react';

import styled from 'styled-components';

import MessageModel from '../models/Message.ts';
import DialogService from '../services/DialogService.ts';
import Message from './Message.tsx';


const DialogPanel = styled.div`
`;


export default function({ threadUID }: { threadUID: string; }) {
    const [messages, setMessages] = useState(null);
    const [selectedMsgs, setSelectedMsgs] = useState([]);

    useEffect(() => {
        (async () => {
            await Promise.all([
                (async () => setMessages(await DialogService.makeDialog(threadUID)))()
            ])
        })();
    }, []);

    const setMsgSelection = async (msgOrder: number, selected: Boolean) => {
        if (selected) {
            await setSelectedMsgs([ ...selectedMsgs, msgOrder ]);
        } else {
            await setSelectedMsgs(selectedMsgs.filter(selectedMsgOrder => selectedMsgOrder !== msgOrder));
        }
    }

    if (messages === null) {
        return <DialogPanel>loading...</DialogPanel>
    }

    console.log(selectedMsgs)

    return <DialogPanel>
        {
            messages.map(msg => <Message
                key={ msg.order } msg={ msg } selected={ selectedMsgs.indexOf(msg.order) !== -1 }
                setSelection={ selected => setMsgSelection(msg.order, selected) }
            />)
        }
    </DialogPanel>
}
