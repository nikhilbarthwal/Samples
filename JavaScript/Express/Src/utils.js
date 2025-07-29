import axios from "axios";

async function postAsync(url, payload) {
    const response = await axios.post(url, JSON.stringify(payload));
    return response.data;
}

async function getAsync(url) {
    const response = await axios.get(url);
    return response.data;
}

export function post(resp, url, payload, handler) {
    postAsync(url, payload).then(handler).catch(err => {
        resp({
            "error": err.message,
            "name": err.name,
            "stack": err.stack
        });
    });
}

export function get(resp, url, handler) {
    getAsync(url).then(handler).catch(err => {
        resp({
            "error": err.message,
            "name": err.name,
            "stack": err.stack
        }) }
    );
}
