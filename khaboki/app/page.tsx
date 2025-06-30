/* eslint-disable @typescript-eslint/no-unused-vars */

"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import { MapPin, Search, Loader2, Star, Clock, DollarSign, Info, RefreshCw } from "lucide-react";
import { SearchFilters } from "@/components/seacrhFilter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";
import { RestaurantCache } from "@/lib/RestaurantCache";
import { EmptyState, LoadingState } from "@/components/Loading";
import { RestaurantGrid } from "@/components/RestaurantGrid";
import { LocationCoordinates, ScrapeResults, SearchFiltersType, Restaurant } from "@/types";
import { DatasetManager } from "@/components/DatasetManager";

export default function Home() {
  const [searchValue, setSearchValue] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [restaurants, setRestaurants] = useState<ScrapeResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState<SearchFiltersType>({
    cuisineType: "",
    minRating: 0,
    maxDeliveryTime: 60,
    platforms: ["foodpanda", "foodi"],
    maxDeliveryFee: 100,
    sortBy: "rating",
  });
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);
  const [cacheInfo, setCacheInfo] = useState<{
    hasCache: boolean;
    age?: number;
    location?: string;
  }>({ hasCache: false });

  const [suggestions, setSuggestions] = useState<
    google.maps.places.AutocompletePrediction[]
  >([]);
  const [showSuggestions, setShowSuggestions] = useState(false);

  // Map refs
  const mapRef = useRef<google.maps.Map | null>(null);
  const markerRef = useRef<google.maps.Marker | null>(null);
  const mapContainerRef = useRef<HTMLDivElement | null>(null);

  // Initialize map
  const initializeMap = useCallback(() => {
    if (!mapContainerRef.current) return;

    // Default center (Dhaka, Bangladesh based on sample coordinates)
    const defaultCenter = { lat: 23.8103, lng: 90.4125 };

    const mapOptions: google.maps.MapOptions = {
      center: defaultCenter,
      zoom: 14,
      styles: [
        {
          featureType: "poi",
          elementType: "labels",
          stylers: [{ visibility: "off" }],
        },
      ],
      mapTypeControl: false,
      streetViewControl: false,
      fullscreenControl: false,
    };

    const map = new window.google.maps.Map(mapContainerRef.current, mapOptions);
    mapRef.current = map;

    // Create a marker
    const marker = new window.google.maps.Marker({
      position: defaultCenter,
      map: map,
      draggable: true,
      animation: window.google.maps.Animation.DROP,
    });
    markerRef.current = marker;

    // Handle marker drag
    marker.addListener("dragend", () => {
      const position = marker.getPosition();
      if (position) {
        setSelectedLocation({
          lat: position.lat(),
          lng: position.lng(),
        });
      }
    });

    map.addListener("click", (e: google.maps.MapMouseEvent) => {
      const clickedLocation = {
        lat: e.latLng!.lat(),
        lng: e.latLng!.lng(),
      };

      setSelectedLocation(clickedLocation);
      marker.setPosition(clickedLocation);
    });

    const inputElement = document.getElementById(
      "location-search"
    ) as HTMLInputElement;
    if (inputElement) {
      const autocompleteOptions: google.maps.places.AutocompleteOptions = {
        fields: ["address_components", "geometry", "name"],
        types: ["address"],
      };

      const autocomplete = new window.google.maps.places.Autocomplete(
        inputElement,
        autocompleteOptions
      );

      autocomplete.bindTo("bounds", map);
      autocompleteRef.current = autocomplete;

      autocomplete.addListener("place_changed", () => {
        const place = autocomplete.getPlace();

        if (!place.geometry || !place.geometry.location) {
          setError("No location details available for this address");
          return;
        }

        const location = {
          lat: place.geometry.location.lat(),
          lng: place.geometry.location.lng(),
        };

        setSelectedLocation(location);
        map.setCenter(location);
        marker.setPosition(location);
        map.setZoom(17);

        setSuggestions([]);
        setShowSuggestions(false);
      });
    }
  }, []);

  // Load Google Maps script
  useEffect(() => {
    const loadGoogleMapsScript = () => {
      const googleMapScript = document.createElement("script");
      googleMapScript.src = `https://maps.googleapis.com/maps/api/js?key=${process.env.NEXT_PUBLIC_GOOGLE_MAPS_API_KEY}&libraries=places&callback=initMap`;
      googleMapScript.async = true;
      googleMapScript.defer = true;
      window.document.body.appendChild(googleMapScript);

      // Define global callback
      window.initMap = initializeMap;

      return () => {
        window.document.body.removeChild(googleMapScript);
        delete window.initMap;
      };
    };

    if (!window.google) {
      loadGoogleMapsScript();
    } else {
      initializeMap();
    }
  }, [initializeMap]);

  const handleSearchInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const value = e.target.value;
    setSearchValue(value);

    if (value.length < 3) {
      setSuggestions([]);
      setShowSuggestions(false);
      return;
    }

    setShowSuggestions(true);
  };

  useEffect(() => {
    const cached = RestaurantCache.load();
    if (cached) {
      setRestaurants(cached.restaurants as ScrapeResults);
      setSelectedLocation(cached.location);
      setSearchValue(cached.searchText);
      setCacheInfo(RestaurantCache.getCacheInfo());
    }
  }, []);

  const fetchRestaurants = async (forceRefresh = false) => {
    // if (!selectedLocation) {
    //   setError("Please select a location first");
    //   return;
    // }

    const currentLocation = selectedLocation || { lat: 23.8103, lng: 90.4125 };
    const currentSearchText = searchValue || "Matikata";

    if (!forceRefresh) {
      const cachedData = RestaurantCache.shouldUseCache(
        currentLocation,
        currentSearchText
      );
      if (cachedData) {
        setRestaurants(cachedData.restaurants);
        setCacheInfo(RestaurantCache.getCacheInfo());
        console.log("Using cached data");
        return;
      }
    }

    setIsLoading(true);
    setError(null);

    try {
      const response = await fetch("http://127.0.0.1:5000/scrape", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          lat: 23.8103,
          lng: 90.4125,
          text: "Matikata",
        }),
        // body: JSON.stringify({
        //   lat: currentLocation.lat,
        //   lng: currentLocation.lng,
        //   text: currentSearchText,
        // }),
      });

      const data = await response.json();

      if (data.success) {
        setRestaurants(data.results);

        RestaurantCache.save({
          restaurants: data.results,
          location: currentLocation,
          searchText: currentSearchText,
          filters,
        });

        setCacheInfo(RestaurantCache.getCacheInfo());
      } else {
        setError(data.error || "Failed to fetch restaurants");
      }
    } catch (err) {
      setError(
        "Failed to connect to server. Please check your internet connection."
      );
      console.error("Error fetching data:", err);
    } finally {
      setIsLoading(false);
    }
  };

  const handleSearchLocation = async (): Promise<void> => {
    if (!window.google || !searchValue) return;

    const geocoder = new window.google.maps.Geocoder();

    geocoder.geocode(
      { address: searchValue },
      (
        results: google.maps.GeocoderResult[] | null,
        status: google.maps.GeocoderStatus
      ) => {
        if (status === "OK" && results && results[0] && results[0].geometry) {
          const location: LocationCoordinates = {
            lat: results[0].geometry.location.lat(),
            lng: results[0].geometry.location.lng(),
          };

          setSelectedLocation(location);

          if (mapRef.current && markerRef.current) {
            mapRef.current.setCenter(location);
            markerRef.current.setPosition(location);
            mapRef.current.setZoom(15);
          }
        } else {
          setError("Location not found. Please try another search term.");
        }
      }
    );
  };

  const handleFilterChange = (newFilters: SearchFiltersType): void => {
    setFilters(newFilters);

    if (restaurants) {
      const filteredResults = applyFilters(restaurants, newFilters);
      setRestaurants(filteredResults);
    }
  };

  const applyFilters = (
    results: ScrapeResults,
    filterOptions: SearchFiltersType
  ): ScrapeResults => {
    const filterRestaurants = (restaurantList: Restaurant[]): Restaurant[] => {
      return restaurantList
        .filter((restaurant) => {
          // Filter by cuisine type
          if (
            filterOptions.cuisineType &&
            !restaurant.cuisine_type
              .toLowerCase()
              .includes(filterOptions.cuisineType.toLowerCase())
          ) {
            return false;
          }

          // Filter by platform
          if (
            !filterOptions.platforms.includes(restaurant.platform.toLowerCase())
          ) {
            return false;
          }

          // Filter by rating
          const rating = parseFloat(restaurant.rating.replace(/[^\d.]/g, ""));
          if (!isNaN(rating) && rating < filterOptions.minRating) {
            return false;
          }

          // Filter by delivery time
          const timeMatch = restaurant.delivery_time.match(/\d+/);
          if (timeMatch) {
            const deliveryTime = parseInt(timeMatch[0]);
            if (deliveryTime > filterOptions.maxDeliveryTime) {
              return false;
            }
          }

          return true;
        })
        .sort((a, b) => {
          // Sort based on selected criteria
          switch (filterOptions.sortBy) {
            case "rating":
              const ratingA = parseFloat(a.rating.replace(/[^\d.]/g, "")) || 0;
              const ratingB = parseFloat(b.rating.replace(/[^\d.]/g, "")) || 0;
              return ratingB - ratingA; // Higher rating first

            case "delivery_time":
              const timeA = parseInt(
                a.delivery_time.match(/\d+/)?.[0] || "999"
              );
              const timeB = parseInt(
                b.delivery_time.match(/\d+/)?.[0] || "999"
              );
              return timeA - timeB; // Faster delivery first

            case "name":
              return a.name.localeCompare(b.name);

            default:
              return 0;
          }
        });
    };

    return {
      foodpanda: results.foodpanda ? filterRestaurants(results.foodpanda) : [],
      foodi: results.foodi ? filterRestaurants(results.foodi) : [],
    };
  };

  const clearCache = () => {
    RestaurantCache.clear();
    setCacheInfo({ hasCache: false });
    setRestaurants(null);
  };

  const hasResults =
    restaurants && (restaurants.foodpanda?.length || restaurants.foodi?.length);

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm border-b">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
          <div className="flex justify-between items-center">
            <div>
              <h1 className="text-3xl font-bold text-gray-900">Khabo ki?</h1>
              <p className="text-gray-600 mt-1">
                Find and compare the best food delivery options
              </p>
            </div>

            {cacheInfo.hasCache && (
              <div className="flex items-center gap-2">
                <Badge variant="outline" className="text-green-600">
                  <Info size={12} className="mr-1" />
                  Cached {cacheInfo.age}m ago
                </Badge>
                <Button variant="ghost" size="sm" onClick={clearCache}>
                  Clear Cache
                </Button>
              </div>
            )}
            <DatasetManager />
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Location selection section */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold">Select your location</h2>
              {hasResults && (
                <Button
                  variant="outline"
                  size="sm"
                  onClick={() => fetchRestaurants(true)}
                  className="flex items-center gap-2"
                >
                  <RefreshCw size={16} />
                  Refresh Results
                </Button>
              )}
            </div>

            {/* Search input */}
            <div className="mb-4 flex">
              <div className="relative flex-grow">
                <div className="relative">
                  <Input
                    id="location-search"
                    placeholder="Enter your address..."
                    value={searchValue}
                    onChange={(e) => setSearchValue(e.target.value)}
                    className="pr-10 rounded-r-none"
                  />
                  <MapPin
                    size={18}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                  />
                </div>
              </div>
              <Button
                onClick={() => fetchRestaurants()}
                disabled={isLoading}
                className="rounded-l-none bg-green-600 hover:bg-green-700"
              >
                {isLoading ? (
                  <Loader2 size={18} className="animate-spin" />
                ) : (
                  <Search size={18} />
                )}
              </Button>
            </div>

            {/* Map container - keeping your existing map code */}
            <div
              ref={mapContainerRef}
              className="w-full h-[300px] rounded-md border border-gray-300"
            ></div>

            {/* Location info */}
            {selectedLocation && (
              <div className="mt-4 flex justify-between items-center">
                <p className="text-sm text-gray-600">
                  Selected: {selectedLocation.lat.toFixed(5)},{" "}
                  {selectedLocation.lng.toFixed(5)}
                </p>
                <Button
                  onClick={() => fetchRestaurants()}
                  disabled={isLoading}
                  className="bg-green-600 hover:bg-green-700"
                >
                  {isLoading ? (
                    <span className="flex items-center">
                      <Loader2 size={18} className="mr-2 animate-spin" />
                      Finding restaurants...
                    </span>
                  ) : (
                    "Find Restaurants"
                  )}
                </Button>
              </div>
            )}
          </CardContent>
        </Card>

        {/* Error message */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {isLoading && <LoadingState />}

        {!isLoading && hasResults && (
          <div className="space-y-6">
            <div className="flex justify-between items-center">
              <div></div>
              <SearchFilters onFilterChange={handleFilterChange} />
            </div>
            <RestaurantGrid restaurants={restaurants!} filters={filters} />
          </div>
        )}

        {!isLoading && !hasResults && restaurants && <EmptyState />}
      </main>
    </div>
  );
}

declare global {
  interface Window {
    google: typeof google;
    initMap?: () => void;
  }
}