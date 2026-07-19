class SimulationProviderError(Exception): pass
class ProviderValidationError(SimulationProviderError): pass
class ProviderCompletenessError(SimulationProviderError): pass
class ProviderUnsupportedError(SimulationProviderError): pass
