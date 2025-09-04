import MessageModel from '../models/Message.ts';
import Message from './Message.tsx';


export default function({ messages }: { messages: MessageModel[] }) {
    return <>
        {
            messages.map(msg => <Message key={msg.order} msg={msg} />)
        }
    </>
}
