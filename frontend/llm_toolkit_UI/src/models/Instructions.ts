import Message from './Message.ts';


export default class Instructions {
    constructor (
        public archiving: Message | null = null
    ) {}

    isFull(): Boolean {
        return this.archiving !== null;
    }
}
