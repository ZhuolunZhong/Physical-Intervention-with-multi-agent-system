import http from "../http-common";

class DataService {

    post(data: any) {
        return http.post<any>("", data);
    }

}

export default new DataService();