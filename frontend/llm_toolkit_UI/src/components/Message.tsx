import styled from 'styled-components';

import MessageModel from '../models/Message.ts';

const Message = styled.div`
    white-space: pre-line;
    border: 1px solid #FFF;
    margin: 10px;
    padding: 10px;
    text-align: left;

    &.user {
        width: 70%;
        margin-left: auto;
    }

    &.selected {
        background-color: #660;
        color: black;
        border-color: #FF0;
    }
`;


export default function(
    { msg, selected, setSelection }: {
        msg: MessageModel; selected: Boolean; setSelection: (selected: boolean) => void;
    }
) {
    return <Message
        className={ msg.role + (selected ? ' selected' : '') } onClick={ () => setSelection(!selected) }
    >
        {msg.text}
    </Message>
}
