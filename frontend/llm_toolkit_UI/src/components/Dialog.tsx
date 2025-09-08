import { useContext, useEffect, useState } from 'react';

import styled from 'styled-components';

import MessageModel from '../models/Message.ts';
import DialogService from '../services/DialogService.ts';
import { ArchivingContext } from "../context/Dialog.tsx";
import Message from './Message.tsx';


const DialogPanel = styled.div`
    flex: 1;
    overflow-y: auto;
    height: 100%;
    padding: 16px;
`;


export default function({ threadUID }: { threadUID: string; }) {
    const [messages, setMessages] = useState(null);
    const {
        selectedOrders: selectedMsgsOrders, setSelectedOrders: setSelectedMsgsOrders
    } = useContext(ArchivingContext);

    useEffect(() => {
        (async () => {
            await Promise.all([
                (async () => setMessages(await DialogService.makeDialog(threadUID)))()
            ])
        })();
    }, []);

    const setMsgSelection = async (msgOrder: number, selected: Boolean) => {
        if (selected) {
            await setSelectedMsgsOrders([ ...selectedMsgsOrders, msgOrder ]);
        } else {
            await setSelectedMsgsOrders(
                selectedMsgsOrders.filter(selectedMsgOrder => selectedMsgOrder !== msgOrder)
            );
        }
    }

    if (messages === null) {
        return <DialogPanel>loading...</DialogPanel>
    }

    console.log(selectedMsgsOrders)

    return <DialogPanel>
        {
            messages.map(msg => <Message
                key={ msg.order } msg={ msg } selected={ selectedMsgsOrders.indexOf(msg.order) !== -1 }
                setSelection={ selected => setMsgSelection(msg.order, selected) }
            />)
        }
    </DialogPanel>
}
