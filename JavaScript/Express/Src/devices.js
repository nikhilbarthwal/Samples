import fs from 'fs';
import * as utils from './utils.js';

const urlAndroid = 'https://iphone.thex.dta.netflix.net';
const urlIphone = 'https://android.thex.dta.netflix.net';
const urlTv = 'https://tv.thex.dta.netflix.net';

// NOTE: In production app, you would create a class hierarchy with separate
//       classes for Android, iPhone, and TV.

class Device {

    constructor(item) {
        this.id = item['devId'];
        this.type = item['type'];
        this.data = item;
        this.inUse = null;
        this.logUrl = null;
        this.stopUrl = null;
    }

    update(resp, status, data) {
        resp({
            "id": this.id,
            "type": this.data['type'],
            "status": status,
            "data": data
        })
    }
}

export class Devices {

    constructor(filename) {
        const data = JSON.parse(fs.readFileSync(filename, 'utf8'));
        const devices = data.map(device => new Device(device));
        this.devices = new Map(devices.map(device => [device.id, device]));
    }

    search(map) {
        let result = this.devices.values().toArray();
        for (const [key, value] of map)
            result = result.filter(x => x.data[key] === value);

        return JSON.stringify(result.map(x => x.id));
    }

    start = (id, session, resp) => {

        if (!this.devices.has(id)) {
            resp({"error": "Device not found!"});
            return;
        }

        const device = this.devices.get(id)

        if (device.inUse === session) {
            resp({"error": "Device already started by the same user!"});
            return;
        }

        if (device.inUse !== null) {
            resp({"error": "Device already started in different session!"});
            return;
        }

        // Assert (device.inUse === null)
        function handler(data) {
            device.inUse = session;
            device.logUrl = (data.has('logUrl')) ? data.get('logUrl') : null;
            device.stopUrl = (data.has('stopUrl')) ? data.get('stopUrl') : null;
            device.update(resp, "started", data)
        }

        function post(url, payload) {
            const p = JSON.stringify(payload);
            console.log(`Connecting to Url = ${url} for ${device.type} device ID: ${device.id} with post payload = ${p}`);
            utils.post(resp, url, payload, handler);
        }

        if (device.type === "iphone") {
            post(`${urlIphone}/launch?id=${device.data['usbAddr']}`, {});
            return;
        }

        if (device.type === "android") {
            post(`${urlAndroid}/start/:${device.data['ipAddr']}`, {});
            return;
        }

        if (device.type === "tv") {
            const payload = {"ipAddr": device.data['ipAddr']};
            post(`${urlTv}/run`, payload);
            return;
        }

        resp({ "error": "Unknown type for device!" });
    }

    stop = (id, session, resp) => {

        if (!this.devices.has(id)) {
            resp({"error": "Device not found!"});
            return;
        }

        const device = this.devices.get(id)

        if (device.inUse !== session) {
            resp({"error": "Device started in different session!"});
            return;
        }

        if (device.inUse === null) {
            resp({"error": "Device not started!"});
            return;
        }

        // Assert (device.inUse === session)
        function handler(data) {
            device.inUse = null;
            device.stopUrl = null;
            device.logUrl = null;
            device.update(resp, "stopped", data)
        }

        function post(url) {
            console.log(`Connecting to Url = ${url} for ${device.type} device ID: ${device.id} with no post payload`);
            utils.post(resp, url, {}, handler);
        }

        if (device.type === "iphone") {
            post(`${urlIphone}/terminate?id=${device.data['usbAddr']}`);
            return;
        }

        if (device.type === "android") {
            post(`${urlAndroid}/stop/:${device.data['ipAddr']}`);
            return;
        }

        if (device.type === "tv") {
            post(device.stopUrl);
            return;
        }

        resp({ "error": "Unknown type for device!" });
    }

    log = (id, session, resp) => {

        if (!this.devices.has(id)) {
            resp({"error": "Device not found!"});
            return;
        }

        const device = this.devices.get(id)

        // Assert (device.inUse === session)

        function handler(data) { device.update(resp, "logs-obtained", data); }

        if (device.inUse !== session) {
            resp({"error": "Device started in different session!"});
            return;
        }

        if (device.inUse === null) {
            resp({"error": "Device not started!"});
            return;
        }

        if (device.type === "iphone") {
            const url = `${urlIphone}/stdout?id=${device.data['usbAddr']}`;
            console.log(`Connecting to Url = ${url} for ${device.type} device ID: ${device.id} with no get payload`);
            utils.get(resp, url, handler);
            return;
        }

        if (device.type === "android") {
            const url = `${urlAndroid}/stop/:${device.data['ipAddr']}`;
            console.log(`Connecting to Url = ${url} for ${device.type} device ID: ${device.id} with no get payload`);
            utils.get(resp, url, handler);
            return;
        }

        if (device.type === "tv") {
            console.log(`Connecting to Url = ${url} for ${device.type} device ID: ${device.id} with no post payload`);
            utils.post(resp,device.logUrl, {}, handler);
            return;
        }

        resp({ "error": "Unknown type for device!" });
    }
}
