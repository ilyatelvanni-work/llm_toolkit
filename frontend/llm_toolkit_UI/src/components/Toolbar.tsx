import { useContext, useEffect, useState } from 'react';

import styled from 'styled-components';

import MessageModel from '../models/Message.ts';
import InstructionsModel from '../models/Instructions.ts';
import DialogService from '../services/DialogService.ts';
import { ArchivingContext } from "../context/Dialog.tsx";
import Message from './Message.tsx';


const Toolbar = styled.aside`
    float: left;
    padding: 10px;
    margin: 10px;
    max-width: 25%;
`;

const Archiving = styled.div`
`;


export default function({ threadUID }: { threadUID: string }) {
    const [instructions, setInstructions] = useState(new InstructionsModel());

    const { selectedOrders: selectedMsgsOrdersForArchiving } = useContext(ArchivingContext);

    useEffect(() => {
        (async () => {
            var instructions_obj = new InstructionsModel()

            await Promise.all([
                (async () =>
                    instructions_obj.archiving = await DialogService.getArchivingInstructionMessage(threadUID)
                )()
            ])

            setInstructions(instructions_obj);
        })();
    }, []);

    if (!instructions.isFull()) {
        return <Toolbar>loading...</Toolbar>
    }

    async function archiveAction() {
        const archive_msg = await DialogService.suggestArchivingMessage(
            threadUID, selectedMsgsOrdersForArchiving
        );
        if (confirm(archive_msg.text)) {
            alert('Done');
        }
    }

    return <Toolbar>
        <Archiving>
            <button onClick={ archiveAction } >Archive</button>
            <Message msg={ instructions.archiving } />
            {
                // messages.map(msg => <Message key={msg.order} msg={msg} />)
            }
        </Archiving>
    </Toolbar>
}
