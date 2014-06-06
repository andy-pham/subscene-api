
# Subscene (unofficial) API

RESTful API for [Subscene](http://subscene.com).
Currently being used by [Popcorn Time](https://github.com/andy-pham/popcorn-app).
Feel free to fork and contribute.

Demo: <http://subscene-api.appspot.com/>


## Retrieve Subtitles

### Request:

```
GET http://subscene-api.appspot.com/subtitles/{imdb_id}
```

```
GET http://subscene-api.appspot.com/subtitles/{imdb_id_1}-{imdb_id_2}-...
```

### Parameters:

- `imdb_id`: The IMDb ID of the movie.

### Examples:

- <http://subscene-api.appspot.com/subtitles/tt0435705>
- <http://subscene-api.appspot.com/subtitles/tt0770828-tt0816442-tt0903624>


## Quick Start

1. Install the [App Engine Python SDK](https://developers.google.com/appengine/downloads).
2. Clone this repo:

    ```
    git clone git@github.com:andy-pham/subscene-api.git
    ```

3. Run locally from the command line:

    ```
    cd subscene-api
    dev_appserver.py .
    ```

Visit subscene-api <http://localhost:8080/>

The admin console is viewable at <http://localhost:8000/>


# Deploy

To deploy subscene-api to App Engine

1. Use the [Admin Console](https://appengine.google.com/) to create a project/app id.
2. Deploy:

    ```
    appcfg.py -A <your-project-id> --oauth2 update .
    ```

subscene-api should be visible at <http://your-app-id.appspot.com/>

# License

Licensed under the [MIT License](http://cheeaun.mit-license.org/).
