import numpy as np
from sklearn.decomposition import PCA
from FileOps import FileReader, FileWriter
from Calculus import Calculator
import Constants as C


class Oracle:
    def __init__(self):
        self.reader = FileReader()
        self.writer = FileWriter()
        self.calc = Calculator()

    def get_filename(self, name):
        return f'models/latest/{name}.pkl'

    def load_model_pickle(self, name):
        filename = self.get_filename(name)
        return self.reader.load_pickle(filename)

    def save_model_pickle(self, name, data):
        filename = self.get_filename(name)
        return self.writer.save_pickle(filename, data)

    def predict(self, data):
        model = self.load_model_pickle('model')
        return model.predict(data)

    def visualize(self, X, y, dimensions, refinement, increase_percent=0):
        # # recommended in the range [4, 100]
        num_points = refinement
        reducer = PCA(n_components=dimensions)
        X_transformed = reducer.fit_transform(X)
        components = X_transformed.T
        all_coords = np.concatenate(X_transformed)
        # or method='mean'
        centroid = self.calc.find_centroid(X_transformed, method='extrema')
        super_min = min(all_coords)
        super_min -= abs(super_min) * increase_percent
        super_max = max(all_coords)
        super_max += abs(super_max) * increase_percent
        radius = (super_max - super_min) / 2
        lins = [np.linspace(
            component - radius if dimensions > 2 else min(components[idx]),
            component + radius if dimensions > 2 else max(components[idx]),
            num_points
        ) for idx, component in enumerate(centroid)]
        unflattened = np.meshgrid(*lins)
        flattened = [arr.flatten() for arr in unflattened]
        reduced = np.array(flattened).T
        unreduced = reducer.inverse_transform(reduced)
        preds = self.predict(unreduced).astype(int)
        actual = [
            {
                C.BUY: [
                    datum for idx, datum in enumerate(component) if y[idx]
                ],
                C.SELL: [
                    datum for idx, datum in enumerate(component) if not y[idx]
                ]
            } for component in components
        ]
        return actual, centroid, radius, flattened, preds
