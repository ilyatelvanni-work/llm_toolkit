
export enum Role {
    assistant = "assistant",
    user = "user",
    system = "system",
};


export default class Message {
    constructor (
        public threadUID: string,
        public order: number,
        public role: Role,
        public text: string
    ) {}

    static fromDTO(dto: Record<string, string | number>): Message {
        return new Message(
            dto.thread_uid,
            dto.order,
            dto.role,
            dto.text
        );
    }   
};
