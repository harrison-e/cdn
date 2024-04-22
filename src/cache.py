# cache.py - contains Cache, for use in src/httpserver.py



# +----------------+
# |  Server Cache  |
# +----------------+
class Cache:
    # -- Constructor -- 
    # > Creates a Cache with the specified arguments 
    def __init__(self, max_size, request_function, refresh_rate, verbose=False):
        # Metadata about files, formatted as 'filepath' : (size, frequency)
        self.metadata = {} 
        # The actual data we've cached, and how big it is
        self.cached_files = {} 
        self.cached_size = 0
        # The maximum size of data cached
        self.max_cache_size = max_size
        # Callback function to request data from origin server 
        self.request_function = request_function
        # After how many requests should the Cache automatically refresh?
        self.request_count = 0
        self.refresh_rate = refresh_rate
        # Run in verbose mode
        self.verbose = verbose

    # -- Log --
    # > Prints a message if the Cache is in verbose mode
    def log(self, message):
        if self.verbose:
            print(message)

    # -- Get --
    # > Retrieves a file from the Cache, or requests file 
    #   using request_function 
    # ! May raise FileNotFoundError (from request_function)
    def get(self, filepath):
        # First, check if we should refresh the Cache 
        self.request_count += 1
        if self.request_count % self.refresh_rate == 0:
            try:
                self.refresh()
            except FileNotFoundError:
                raise

        # See if we've already cached this file 
        if filepath in self.cached_files:
            # If we've already cached it, it has metadata (that needs updating)
            size, freq = self.metadata[filepath]
            self.metadata[filepath] = (size, freq + 1) 
            # Use our cached files!
            return self.cached_files[filepath]

        # If not, try and get it 
        try:
            data = self.request_function(filepath)
        except FileNotFoundError:
            raise 

        # And see if we can cache it
        size = len(data)
        if self.cached_size + size < self.max_cache_size:
            self.cached_files[filepath] = data
            self.cached_size += size
        
        # Update metadata
        if filepath not in self.metadata:
            self.metadata[filepath] = (len(data), 1)
        else:
            size, freq = self.metadata[filepath]
            self.metadata[filepath] = (size, freq + 1) 

        # Finally, return our data
        return data
    
    # -- Refresh -- 
    # > Refreshes the cache, caching the highest priority 
    #   files that can fit 
    # > Priority is the product of a file's size, and how 
    #   many times it has been requested 
    # ! May raise FileNotFoundError (from request_function)
    def refresh(self):
        self.log(f'Old cache: {self.cached_files}, Size: {self.cached_size}/{self.max_cache_size}')
        # Order encountered files by Priority (size * frequency)
        priority_files = sorted(self.metadata, 
                                key=lambda f : self.metadata[f][0] * self.metadata[f][1], 
                                reverse=True)
        self.log(f'Metadata: {self.metadata}')
        self.log(f'Priority: {priority_files}')
        current_cache = self.cached_files.keys()
        new_cache = []
        new_cache_size = 0
        
        # As long as we have space, add high priority files
        for filepath in priority_files:
            if new_cache_size == self.max_cache_size:
                break
            size, freq = self.metadata[filepath]
            if new_cache_size + size < self.max_cache_size:
                new_cache.append(filepath)
                new_cache_size += size

        # Remove files that are low Priority
        to_remove = current_cache - new_cache
        for filepath in to_remove:
            del self.cached_files[filepath]
        
        # Cache files that are not already cached
        for filepath in new_cache:
            if filepath not in self.cached_files:
                try:
                    self.cached_files[filepath] = self.request_function(filepath) 
                except FileNotFoundError:
                    raise
        self.cached_size = new_cache_size
        self.log(f'New cache: {self.cached_files}, Size: {self.cached_size}/{self.max_cache_size}\n')
