from tensorflow.keras.layers import Input, Conv3D, MaxPooling3D, UpSampling3D, SpatialDropout3D, concatenate
from tensorflow.keras.models import Model

from nobrainer.layers.groupnorm import GroupNormalization


def down_stage(inputs, filters, kernel_size=3,
               activation="relu", padding="SAME"):
    conv = Conv3D(filters, kernel_size,
                  activation=activation, padding=padding)(inputs)
    conv = GroupNormalization()(conv)
    conv = Conv3D(filters, kernel_size,
                  activation=activation, padding=padding)(conv)
    conv = GroupNormalization()(conv)
    pool = MaxPooling3D()(conv)
    return conv, pool


def up_stage(inputs, skip, filters, kernel_size=3,
             activation="relu", padding="SAME"):
    up = UpSampling3D()(inputs)
    up = Conv3D(filters, 2, activation=activation, padding=padding)(up)
    up = GroupNormalization()(up)

    merge = concatenate([skip, up])
    merge = GroupNormalization()(merge)

    conv = Conv3D(filters, kernel_size,
                  activation=activation, padding=padding)(merge)
    conv = GroupNormalization()(conv)
    conv = Conv3D(filters, kernel_size,
                  activation=activation, padding=padding)(conv)
    conv = GroupNormalization()(conv)
    conv = SpatialDropout3D(0.5)(conv, training=True)

    return conv


def end_stage(inputs, kernel_size=3, activation="relu", padding="SAME"):
    conv = Conv3D(1, kernel_size, activation=activation, padding="SAME")(inputs)
    conv = Conv3D(1, 1, activation="sigmoid")(conv)

    return conv


def dropout_vnet(input_shape=(280, 280, 280, 1), kernel_size=3,
                 activation="relu", padding="SAME", **kwargs):
    inputs = Input(input_shape)

    conv1, pool1 = down_stage(inputs, 16,
                              kernel_size=kernel_size,
                              activation=activation,
                              padding=padding)
    conv2, pool2 = down_stage(pool1, 32,
                              kernel_size=kernel_size,
                              activation=activation,
                              padding=padding)
    conv3, pool3 = down_stage(pool2, 64,
                              kernel_size=kernel_size,
                              activation=activation,
                              padding=padding)
    conv4, _ = down_stage(pool3, 128,
                          kernel_size=kernel_size,
                          activation=activation,
                          padding=padding)
    conv4 = SpatialDropout3D(0.5)(conv4, training=True)

    conv5 = up_stage(conv4, conv3, 64,
                     kernel_size=kernel_size,
                     activation=activation,
                     padding=padding)
    conv6 = up_stage(conv5, conv2, 32,
                     kernel_size=kernel_size,
                     activation=activation,
                     padding=padding)
    conv7 = up_stage(conv6, conv1, 16,
                     kernel_size=kernel_size,
                     activation=activation,
                     padding=padding)

    conv8 = end_stage(conv7, kernel_size=kernel_size,
                      activation=activation, padding=padding)

    return Model(inputs=inputs, outputs=conv8)
