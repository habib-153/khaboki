/* eslint-disable @typescript-eslint/no-unused-vars */
/* eslint-disable @typescript-eslint/no-explicit-any */
"use client";

import { useState, useEffect, useRef, useCallback } from "react";
import Image from "next/image";
import { MapPin, Search, Loader2, Star, Clock, DollarSign } from "lucide-react";
import { SearchFilters } from "@/components/seacrhFilter";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import {
  Card,
  CardContent,
  CardFooter,
  CardHeader,
} from "@/components/ui/card";
import { Alert, AlertDescription } from "@/components/ui/alert";
import { Badge } from "@/components/ui/badge";

// Type definitions
interface Restaurant {
  name: string;
  cuisine_type: string;
  rating: string;
  delivery_time: string;
  delivery_fee: string;
  platform: string;
  image_url: string;
  url: string;
  menu_items: any[];
}

interface ScrapeResults {
  foodpanda: Restaurant[];
  // Add other platforms here as needed
}

export default function Home() {
  const [searchValue, setSearchValue] = useState<string>("");
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [selectedLocation, setSelectedLocation] = useState<{
    lat: number;
    lng: number;
  } | null>(null);
  const [restaurants, setRestaurants] = useState<ScrapeResults | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [filters, setFilters] = useState({});
  const autocompleteRef = useRef<google.maps.places.Autocomplete | null>(null);

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

  const fetchRestaurants = async () => {
    if (!selectedLocation) {
      setError("Please select a location first");
      return;
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
          lat: selectedLocation.lat,
          lng: selectedLocation.lng,
        }),
      });

      const data = await response.json();

      if (data.success) {
        setRestaurants(data.results);
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

  const handleSearchLocation = async () => {
    if (!window.google || !searchValue) return;

    const geocoder = new window.google.maps.Geocoder();
    geocoder.geocode({ address: searchValue }, (results, status) => {
      if (status === "OK" && results && results[0] && results[0].geometry) {
        const location = {
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
    });
  };

  const handleFilterChange = (newFilters: any) => {
    setFilters(newFilters);
    // implement filtering logic here
  };

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Header */}
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex justify-between items-center">
          <h1 className="text-2xl font-bold text-gray-900">Khabo ki?</h1>
          <p className="text-sm text-gray-500">Find the best food near you</p>
        </div>
      </header>

      {/* Main content */}
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Location selection section */}
        <Card className="mb-8">
          <CardContent className="p-6">
            <h2 className="text-lg font-semibold mb-4">Select your location</h2>

            {/* Search input */}
            <div className="mb-4 flex">
              <div className="relative flex-grow">
                <div className="relative">
                  <Input
                    id="location-search"
                    placeholder="Enter your address..."
                    value={searchValue}
                    onChange={handleSearchInputChange}
                    onFocus={() => {
                      if (searchValue.length >= 3) {
                        setShowSuggestions(true);
                      }
                    }}
                    onBlur={() => {
                      setTimeout(() => setShowSuggestions(false), 200);
                    }}
                    className="pr-10 rounded-r-none"
                  />
                  <MapPin
                    size={18}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400"
                  />
                </div>
              </div>
              <Button
                onClick={handleSearchLocation}
                className="rounded-l-none"
                variant="default"
              >
                <Search size={18} />
              </Button>
            </div>

            {/* Map container */}
            <div
              ref={mapContainerRef}
              className="w-full h-[350px] rounded-md border border-gray-300"
            ></div>

            {/* Location action buttons */}
            <div className="mt-4 flex justify-between">
              <div>
                {selectedLocation && (
                  <p className="text-sm text-gray-600">
                    Selected: {selectedLocation.lat.toFixed(5)},{" "}
                    {selectedLocation.lng.toFixed(5)}
                  </p>
                )}
              </div>
              <Button
                onClick={fetchRestaurants}
                //disabled={!selectedLocation || isLoading}
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
          </CardContent>
        </Card>

        {/* Error message */}
        {error && (
          <Alert variant="destructive" className="mb-6">
            <AlertDescription>{error}</AlertDescription>
          </Alert>
        )}

        {/* Restaurant results */}
        {restaurants && (
          <section>
            <div className="flex justify-between items-center mb-4">
              <h2 className="text-lg font-semibold">Restaurants near you</h2>
              <SearchFilters onFilterChange={handleFilterChange} />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {restaurants.foodpanda &&
                restaurants.foodpanda.map((restaurant, index) => (
                  <Card key={index} className="overflow-hidden">
                    <div className="relative h-40">
                      <Image
                        src={
                          restaurant.image_url ||
                          "https://via.placeholder.com/300x150?text=No+Image"
                        }
                        alt={restaurant.name}
                        fill
                        className="object-cover"
                        sizes="(max-width: 768px) 100vw, (max-width: 1200px) 50vw, 33vw"
                      />
                      <Badge className="absolute top-2 right-2">
                        {restaurant.platform}
                      </Badge>
                    </div>

                    <CardHeader className="p-4 pb-0">
                      <h3 className="font-semibold text-lg truncate">
                        {restaurant.name}
                      </h3>
                      <p className="text-sm text-gray-600">
                        {restaurant.cuisine_type}
                      </p>
                    </CardHeader>

                    <CardContent className="p-4">
                      <div className="flex justify-between items-center text-sm">
                        <div className="flex items-center">
                          <Star size={16} className="text-yellow-500 mr-1" />
                          <span>{restaurant.rating}</span>
                        </div>

                        <div className="flex items-center">
                          <Clock size={16} className="text-gray-400 mr-1" />
                          <span>{restaurant.delivery_time}</span>
                        </div>

                        <div className="flex items-center">
                          <DollarSign
                            size={16}
                            className="text-gray-400 mr-1"
                          />
                          <span>{restaurant.delivery_fee}</span>
                        </div>
                      </div>
                    </CardContent>

                    <CardFooter className="p-4 pt-0">
                      <a
                        href={restaurant.url}
                        target="_blank"
                        rel="noopener noreferrer"
                        className="w-full"
                      >
                        <Button variant="outline" className="w-full">
                          View on {restaurant.platform}
                        </Button>
                      </a>
                    </CardFooter>
                  </Card>
                ))}
            </div>
          </section>
        )}
      </main>
    </div>
  );
}

// Add TypeScript declarations for global Google Maps callback
declare global {
  interface Window {
    google: typeof google;
    initMap?: () => void;
  }
}