
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
        public text: string,
        public archiveFor: number[]
    ) {}

    static fromDTO(dto: Record<string, string | number>): Message {
        return new Message(
            dto.thread_uid,
            dto.order,
            dto.role,
            dto.text,
            dto.archive_for
        );
    }

    toDTO(): Record<string, string | number> {
        const msg_dto = { ...this };
        msg_dto['thread_uid'] = this.threadUID;
        msg_dto['archive_for'] = this.archiveFor;

        return msg_dto;
    }
};
