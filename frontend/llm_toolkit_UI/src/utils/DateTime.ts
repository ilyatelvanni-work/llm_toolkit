export type ISOTimeString = string & { __type: 'ISOTime' };
export type ISODateTimeString = string & { __type: 'ISODateTimeString' };

export const SECONDS_IN_DAY = 24 * 60 * 60;


export function getClientTimezoneOffset(): ISOTimeString {
    const offsetMinutes = new Date().getTimezoneOffset();
    const sign = offsetMinutes > 0 ? "-" : "+";

    const absMinutes = Math.abs(offsetMinutes);
    const hours = String(Math.floor(absMinutes / 60)).padStart(2, "0");
    const minutes = String(absMinutes % 60).padStart(2, "0");

    return `${sign}${hours}:${minutes}` as ISOTimeString;
}


export class Time {
    private value: number

    constructor(value: ISOTimeString | number) {
        if (typeof value === 'string') {
            const [h, m, s = 0] = value.split(":").map(Number)
            this.value = h * 3600 + m * 60 + s;
        } else if (typeof value === 'number') {
            this.value = value
        } else {
            throw `Trying to make ISOTime from "${value}" of ${typeof value} type. Unsupported`
        }
    }

    toString(): ISOTimeString {
        const hh = String(Math.floor(this.value / 3600)).padStart(2, '0');
        const mm = String(Math.floor((this.value % 3600) / 60)).padStart(2, '0');
        const ss = String(this.value % 60).padStart(2, '0');

        return `${hh}:${mm}:${ss}` as ISOTimeString;
    }

    add(otherTime: Time) {
        return new Time(this.value, otherTime.value)
    }

    static sumTimes(...timeValues: Time[]): Time {
        return new Time(timeValues.map(time => time.value).reduce((acc, sec) => acc + sec, 0))
    }
}
