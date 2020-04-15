
import torch

from slovnet.visitor import Visitor
from slovnet.exec import model as exec


class ExecVisitor(Visitor):
    def visit_Parameter(self, item):
        return self.visit(item.data)

    def visit_Tensor(self, item):
        array = item.detach().numpy()
        return exec.Weight(
            array.shape,
            array.dtype.name,
            array
        )

    def visit_Linear(self, item):
        # in torch linear is xA^T + b
        weight = item.weight.transpose(1, 0)
        return exec.Linear(
            self.visit(weight),
            self.visit(item.bias)
        )

    def visit_Conv1d(self, item):
        padding, = item.padding  # tuple -> int
        return exec.Conv1d(
            self.visit(item.weight),
            self.visit(item.bias),
            padding
        )

    def visit_ReLU(self, item):
        return exec.ReLU()

    def visit_BatchNorm1d(self, item):
        running_std = torch.sqrt(item.running_var + item.eps)
        return exec.BatchNorm1d(
            self.visit(item.weight),
            self.visit(item.bias),
            self.visit(item.running_mean),
            self.visit(running_std),
        )

    def visit_Embedding(self, item):
        return exec.Embedding(
            self.visit(item.weight)
        )

    def visit_NavecEmbedding(self, item):
        # recover initial qdim x centroids x chunk
        codes = item.codes.transpose(1, 0)
        return exec.NavecEmbedding(
            item.id,
            self.visit(item.indexes),
            self.visit(codes)
        )

    def visit_TagEmbedding(self, item):
        return exec.TagEmbedding(
            self.visit(item.word),
            self.visit(item.shape)
        )

    def visit_TagEncoderLayer(self, item):
        return exec.TagEncoderLayer(
            self.visit(item.conv),
            self.visit(item.relu),
            self.visit(item.norm)
        )

    def visit_TagEncoder(self, item):
        return exec.TagEncoder([
            self.visit(_)
            for _ in item.layers
        ])

    def visit_NERHead(self, item):
        return exec.NERHead(
            self.visit(item.proj),
            self.visit(item.crf)
        )

    def visit_NER(self, item):
        return exec.NER(
            self.visit(item.emb),
            self.visit(item.encoder),
            self.visit(item.ner)
        )

    def visit_MorphHead(self, item):
        return exec.MorphHead(
            self.visit(item.proj)
        )

    def visit_Morph(self, item):
        return exec.Morph(
            self.visit(item.emb),
            self.visit(item.encoder),
            self.visit(item.morph)
        )

    def visit_CRF(self, item):
        return exec.CRF(
            self.visit(item.transitions)
        )


class ExecMixin:
    @property
    def as_exec(self):
        visitor = ExecVisitor()
        return visitor(self)