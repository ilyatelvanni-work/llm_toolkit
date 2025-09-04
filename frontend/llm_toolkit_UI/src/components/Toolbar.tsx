import { useState, useEffect } from 'react';

import styled from 'styled-components';

import MessageModel from '../models/Message.ts';
import InstructionsModel from '../models/Instructions.ts';
import DialogService from '../services/DialogService.ts';
import Message from './Message.tsx';


const Toolbar = styled.aside`
    float: left;
    padding: 10px;
    margin: 10px;
    max-width: 25%;
`;

const Archiving = styled.div`
    white-space: pre-line;
    text-align: left;
`;


export default function({ threadUID }: { threadUID: string }) {
    const [instructions, setInstructions] = useState(new InstructionsModel());

    useEffect(() => {
        (async () => {
            var instructions_obj = new InstructionsModel()

            await Promise.all([
                (async () => instructions_obj.archiving=await DialogService.makeArchivingMessage(threadUID))()
            ])

            setInstructions(instructions_obj);
        })();
    }, []);

    if (!instructions.isFull()) {
        return <Toolbar>loading...</Toolbar>
    }

    return <Toolbar>
        <Message msg={ instructions.archiving } />
        {
            // messages.map(msg => <Message key={msg.order} msg={msg} />)
        }
    </Toolbar>
}
