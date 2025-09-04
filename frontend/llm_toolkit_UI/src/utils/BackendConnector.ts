import { v4 as uuidv4 } from 'uuid';

const BACKEND_URI = `${(() => { return import.meta.env.VITE_BACKEND_URI })()}`;


export async function http_request(route, fetch_generator) {
    try {
        const requestUUID = uuidv4();
        const response = await fetch_generator(requestUUID)
        if (!response.ok) {
            console.log('HTTP error body:');
            console.log(await response.json());
            throw new Error(`HTTP error! status: ${response.status}`);
        }
        const result = await response.json();
        console.log(`Response ${requestUUID} from server:`);
        console.log(result)
        return result;
    } catch (error) {
        console.error("Error fetching data:", error);
    }
}


export async function getData(route, params) {
    const fetch_generator = (
        (route, params) => (async (requestUUID) => {
            const request = `${route}?${new URLSearchParams(params)}`;
            console.log(`Request ${requestUUID} to server: ${BACKEND_URI}${request}`);
            return await fetch(`${BACKEND_URI}${request}`);
        })
    )(route, params);

    return await http_request(route, fetch_generator);
}


export async function postData(route, body) {
    const fetch_generator = (
        (route, body) => (async (requestUUID) => {
            const str_body = JSON.stringify(body);
            console.log(`Request  ${requestUUID} to server: ${route} with body ${str_body}`);
            return await fetch(`${BACKEND_URI}${route}`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: str_body
            });
        })
    )(route, body);

    return await http_request(route, fetch_generator);
}
