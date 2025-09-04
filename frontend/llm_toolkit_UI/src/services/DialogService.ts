import { getData } from '../utils/BackendConnector.ts';

import Message from '../models/Message.ts';


export default class DialogService {
    static async makeDialog(thread_uid: string): Message[] {
        const messages = await getData(`/threads/${thread_uid}/messages`);

        return messages.map(msg => Message.fromDTO(msg));
    }

    static async makeArchivingMessage(thread_uid: string): Message {
        const message = await getData(`/threads/${thread_uid}/instructions/archiving`);

        return Message.fromDTO(message);
    }
}
