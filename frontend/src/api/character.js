import http from "./http";

export const characterApi = {
  // Get character list
  getList(params) {
    return http.get("/character/list", { params });
  },

  // Get character detail
  getDetail(id) {
    return http.get(`/character/${id}`);
  },

  // Create character
  create(data) {
    return http.post("/character", data);
  },

  // Update character
  update(id, data) {
    return http.put(`/character/${id}`, data);
  },

  // Delete character
  delete(id) {
    return http.delete(`/character/${id}`);
  },

  // Like/Unlike character
  like(id) {
    return http.post(`/character/${id}/like`);
  },

  // Collect/Uncollect character
  collect(id) {
    return http.post(`/character/${id}/collect`);
  },

  // Get my characters
  getMyList(params) {
    return http.get("/character/my", { params });
  },

  // Upload avatar
  uploadAvatar(file) {
    const formData = new FormData();
    formData.append('file', file);
    return http.post("/character/upload", formData, {
      headers: {
        'Content-Type': 'multipart/form-data'
      }
    });
  },
};
