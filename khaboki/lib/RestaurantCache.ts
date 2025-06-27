/* eslint-disable @typescript-eslint/no-explicit-any */
import { ScrapeResults } from "@/app/page";

interface CacheData {
  restaurants: ScrapeResults;
  location: { lat: number; lng: number };
  searchText: string;
  timestamp: number;
  filters?: any;
}

const CACHE_KEY = "khabo-ki-cache";
const CACHE_DURATION = 30 * 60 * 1000; 

export class RestaurantCache {
  static save(data: Omit<CacheData, "timestamp">) {
    const cacheData: CacheData = {
      ...data,
      timestamp: Date.now(),
    };
    try {
      localStorage.setItem(CACHE_KEY, JSON.stringify(cacheData));
    } catch (error) {
      console.error("Error saving to cache:", error);
    }
  }
  static load(): CacheData | null {
    try {
      const cached = localStorage.getItem(CACHE_KEY);
      if (!cached) return null;

      const data: CacheData = JSON.parse(cached);
      if (Date.now() - data.timestamp > CACHE_DURATION) {
        this.clear();
        return null;
      }
      return data;
    } catch (error) {
      console.error("Error loading from cache:", error);
      return null;
    }
  }
  static isLocationSimilar(
    location1: { lat: number; lng: number },
    location2: { lat: number; lng: number },
    threshold = 0.001
  ): boolean {
    const latDiff = Math.abs(location1.lat - location2.lat);
    const lngDiff = Math.abs(location1.lng - location2.lng);

    return latDiff <= threshold && lngDiff <= threshold;
  }
  static shouldUseCache(
    currentLocation: { lat: number; lng: number },
    currentSearchText: string
  ): CacheData | null {
    const cached = this.load();
    if (!cached) return null;

    const locationSimilar = this.isLocationSimilar(
      cached.location,
      currentLocation
    );
    const searchSimilar =
      cached.searchText.toLowerCase() === currentSearchText.toLowerCase();

    return locationSimilar && searchSimilar ? cached : null;
  }
  static clear() {
    try {
      localStorage.removeItem(CACHE_KEY);
    } catch (error) {
      console.error("Error clearing cache:", error);
    }
  }
  static getCacheInfo(): {
    hasCache: boolean;
    age?: number;
    location?: string;
  } {
    const cached = this.load();
    if (!cached) return { hasCache: false };

    const age = Math.floor((Date.now() - cached.timestamp) / 1000 / 60);
    return {
      hasCache: true,
      age,
      location: cached.searchText,
    };
  }
}
