query = '''
                        query ($character: String){
                          Character(search: $character) {
                            id
                            name {
                              first
                              last
                              full
                              native
                            }
                            image {
                              large
                              medium
                            }
                            description
                            media(sort:POPULARITY_DESC) {
                              edges {
                                id
                                node {
                                  id
                                  siteUrl
                                  title {
                                    romaji
                                    english
                                    native
                                    userPreferred
                                  }
                                }
                              }
                            }
                            favourites
                            siteUrl
                          }
                        }
        '''

query_pages = '''
                        query ($character: String, $page: Int, $amount: Int){
                          Page(page: $page, perPage: $amount) {
                            pageInfo {
                              total
                              perPage
                              currentPage
                              lastPage
                              hasNextPage
                            }
                            characters(search: $character) {
                                id
                                name {
                                  first
                                  last
                                  full
                                  native
                                }
                                image {
                                  large
                                  medium
                                }
                                description
                                media(sort:POPULARITY_DESC) {
                                  edges {
                                    id
                                    node {
                                      id
                                      siteUrl
                                      title {
                                        romaji
                                        english
                                        native
                                        userPreferred
                                      }
                                    }
                                  }
                                }
                                favourites
                                siteUrl
                              }
                          }
                        }
        '''