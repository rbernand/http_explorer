class HTTPElement:
    def __init__(self, tag):
        self._type = tag.xpath('td[1]/img')[0].get('alt')
        self._name = tag.xpath('td[2]/a/text()')[0]
        self._url = tag.xpath('td[2]/a/@href')[0]

    @property
    def url(self):
        return self._url

    @property
    def name(self):
        return self._name

    @property
    def type(self):
        return self._type

    def __str__(self):
        return "{} {}".format(self._type, self._name)

    def __repr__(self):
        return "<{type} - {url}>".format(
            type=self.type,
            url=self.name)

    def isdir(self):
        return self._type in ('[DIR]', '[PARENTDIR]')
