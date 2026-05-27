import http from "./http";

export const characterApi = {
  getList(params) {
    return http.get("/character/list", { params });
  },

  getDetail(id) {
    return http.get(`/character/${id}`);
  },

  /** Get character chat config (system prompt + metadata) */
  getChatConfig(id) {
    return http.get(`/character/${id}/config`);
  },

  create(data) {
    return http.post("/character", data);
  },

  update(id, data) {
    return http.put(`/character/${id}`, data);
  },

  delete(id) {
    return http.delete(`/character/${id}`);
  },

  like(id) {
    return http.post(`/character/${id}/like`);
  },

  collect(id) {
    return http.post(`/character/${id}/collect`);
  },

  getMyList(params) {
    return http.get("/character/my", { params });
  },

  uploadAvatar(file) {
    const formData = new FormData();
    formData.append('file', file);
    return http.post("/character/upload", formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },

  /** SSE streaming chat with a character */
  sendChat(characterId, data) {
    return http.post(`/character/${characterId}/chat`, data, {
      responseType: 'stream',
    });
  },
};
