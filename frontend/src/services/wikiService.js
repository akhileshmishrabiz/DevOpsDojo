import API_URL from '../config/api';

export const fetchAllWikiPages = async (category = null) => {
  try {
    const url = category 
      ? `${API_URL}/api/wiki?category=${encodeURIComponent(category)}`
      : `${API_URL}/api/wiki`;
      
    const response = await fetch(url);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching wiki pages:', error);
    throw error;
  }
};

export const fetchWikiPage = async (slug) => {
  try {
    const response = await fetch(`${API_URL}/api/wiki/${slug}`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error(`Error fetching wiki page ${slug}:`, error);
    throw error;
  }
};

export const fetchWikiCategories = async () => {
  try {
    const response = await fetch(`${API_URL}/api/wiki/categories`);
    if (!response.ok) {
      throw new Error(`HTTP error! status: ${response.status}`);
    }
    return await response.json();
  } catch (error) {
    console.error('Error fetching wiki categories:', error);
    throw error;
  }
};

export const createWikiPage = async (pageData) => {
  try {
    const response = await fetch(`${API_URL}/api/wiki`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(pageData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error('Error creating wiki page:', error);
    throw error;
  }
};

export const updateWikiPage = async (slug, pageData) => {
  try {
    const response = await fetch(`${API_URL}/api/wiki/${slug}`, {
      method: 'PUT',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify(pageData),
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`Error updating wiki page ${slug}:`, error);
    throw error;
  }
};

export const deleteWikiPage = async (slug) => {
  try {
    const response = await fetch(`${API_URL}/api/wiki/${slug}`, {
      method: 'DELETE',
    });
    
    if (!response.ok) {
      const errorData = await response.json();
      throw new Error(errorData.error || `HTTP error! status: ${response.status}`);
    }
    
    return true;
  } catch (error) {
    console.error(`Error deleting wiki page ${slug}:`, error);
    throw error;
  }
};