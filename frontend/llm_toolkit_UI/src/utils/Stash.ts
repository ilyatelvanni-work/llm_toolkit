import { ISODateTimeString } from './DateTime.ts'


const _STASH = (() => {
    const stashingMethodObject = (() => {
        if (typeof localStorage !== 'undefined') {
            return localStorage;
        } else if (typeof window && window.localStorage) {
            return window.localStorage
        }

        if (document.cookie) {
            return {
                getItem: (key) => {
                    const cookies = document.cookie.split('; ');
                    const cookie = cookies.find(cookie => cookie.startsWith(`${key}=`));
                    return cookie ? cookie.split('=')[1] : null;
                },
                setItem: (key, value) => {
                    document.cookie = `${key}=${value}; path=/; max-age=31536000`;
                }
            }
        }

        return {
            getItem: (key) => undefined,
            setItem: (key, value) => undefined
        }
    })();

    return {
        setItem: (key, value) => stashingMethodObject.setItem(key, value),
        getItem: (key) => {
            const result = stashingMethodObject.getItem(key);
            return result === 'null' ? null : result;
        }
    };
})();


export class ActivityStash {
    private _selectedActivityIdStartHash: [number, ISODateTimeString]
    private _logsToSendBuffer: [int, ISODateTimeString, ISODateTimeString][]

    static #instance = null;
    static #STASH_SELECT_ACTIVITY_START_HASH_KEY = 'SELECT_ACTIVITY_START_HASH_KEY'
    static #STASH_LOGS_TO_SEND_BUFFER_KEY = 'LOGS_TO_SEND_BUFFER'

    static #STASH_CONFIG_KEY_ATTRIBUTE_MAP = [
        { key: ActivityStash.#STASH_SELECT_ACTIVITY_START_HASH_KEY, prop: '_selectedActivityIdStartHash', def: '{}' },
        { key: ActivityStash.#STASH_LOGS_TO_SEND_BUFFER_KEY, prop: '_logsToSendBuffer', def: '[]' }
    ];

    constructor() {
        if (ActivityStash.#instance) return ActivityStash.#instance;
        ActivityStash.#instance = this;

        for (const { key, prop, def } of ActivityStash.#STASH_CONFIG_KEY_ATTRIBUTE_MAP) {
            const stashValue = JSON.parse(_STASH.getItem(key));

            if (stashValue === null) {
                _STASH.setItem(key, (this[prop] = def));
            } else {
                this[prop] = stashValue;
            }
        }
    }

    addSelectActivityStart(activityId: number, isoTime: Date) {
        if (!(isoTime instanceof Date)) {
            throw `Trying to store ${typeof isoTime} type "${isoTime}" in stash for activity ${activityId}`
        }

        const stash_key = ActivityStash.#STASH_SELECT_ACTIVITY_START_HASH_KEY
        const selectActivityStartHash = JSON.parse(_STASH.getItem(stash_key))
        if (activityId in selectActivityStartHash) {
            throw `trying to add select to already selected activity ${activityId}`
        }

        selectActivityStartHash[activityId] = isoTime.toISOString()
        _STASH.setItem(stash_key, JSON.stringify(selectActivityStartHash))
    }

    getSelectActivityStartTime(activityId: number): Date | null {
        const startTimeString = this._selectedActivityIdStartHash[activityId]
        return startTimeString ? new Date(startTimeString) : null
    }

    removeSelectActivityStart(activityId: number) {
        const activityIdStartHash = this._selectedActivityIdStartHash;
        delete activityIdStartHash[activityId]
        _STASH.setItem(ActivityStash.#STASH_SELECT_ACTIVITY_START_HASH_KEY, JSON.stringify(activityIdStartHash))
    }
}
