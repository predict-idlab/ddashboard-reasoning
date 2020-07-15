class Anomaly(object):
    atypes = ['http://IBCNServices.github.io/Folio-Ontology/Folio.owl#Anomaly']


class UnknownPatternAnomaly(Anomaly):
    def __init__(self):
        super(UnknownPatternAnomaly, self).__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://IBCNServices.github.io/Folio-Ontology/Folio.owl#UnknownPatternAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super(UnknownPatternAnomaly, self).atypes + \
                           ['http://IBCNServices.github.io/Folio-Ontology/Folio.owl#UnknownPatternAnomaly']
        return self._atypes


class KnownPatternAnomaly(Anomaly):
    def __init__(self):
        super(KnownPatternAnomaly, self).__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://IBCNServices.github.io/Folio-Ontology/Folio.owl#KnownPatternAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super(KnownPatternAnomaly, self).atypes + \
                           ['http://IBCNServices.github.io/Folio-Ontology/Folio.owl#KnownPatternAnomaly']
        return self._atypes


class ConfirmedAnomaly(Anomaly):
    def __init__(self):
        super().__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://IBCNServices.github.io/Folio-Ontology/Folio.owl#ConfirmedAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super().atypes + \
                           ['http://IBCNServices.github.io/Folio-Ontology/Folio.owl#ConfirmedAnomaly']
        return self._atypes


class MergedAnomaly(ConfirmedAnomaly):
    def __init__(self):
        super().__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://IBCNServices.github.io/Folio-Ontology/Folio.owl#MergedAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super().atypes + \
                           ['http://IBCNServices.github.io/Folio-Ontology/Folio.owl#MergedAnomaly']
        return self._atypes


class RelabeledAnomaly(ConfirmedAnomaly):
    def __init__(self):
        super().__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://IBCNServices.github.io/Folio-Ontology/Folio.owl#RelabeledAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super().atypes + \
                           ['http://IBCNServices.github.io/Folio-Ontology/Folio.owl#RelabeledAnomaly']
        return self._atypes


class UnknownRoomAnomaly(Anomaly):
    def __init__(self):
        super(UnknownRoomAnomaly, self).__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://renson#UnexpectedRoomTypeAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super(UnknownRoomAnomaly, self).atypes + \
                           ['http://renson#UnexpectedRoomTypeAnomaly']
        return self._atypes


class TrackIssueAnomaly(Anomaly):
    def __init__(self):
        super(TrackIssueAnomaly, self).__init__()
        self._atypes = None

    @property
    def atype(self):
        return 'http://televic#TrackIssueAnomaly'

    @property
    def atypes(self):
        if self._atypes is None:
            self._atypes = super(TrackIssueAnomaly, self).atypes + \
                           ['http://televic#TrackIssueAnomaly']
        return self._atypes


if __name__ == '__main__':
    a = RelabeledAnomaly()
    print(a.atypes)
