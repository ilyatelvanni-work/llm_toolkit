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
`;


export default function({ msg }: { msg: MessageModel }) {
    return <Message className={ msg.role }>
        {msg.text}
    </Message>
}
